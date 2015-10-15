import ConfigParser
import random
import os
import collections
import sys
import json
import time
import datetime

import numpy

from .person import Person
from . import utils
from . import reports
from .decorators import read_or_run


class Datascope(object):

    def __init__(self):

        # instantiate the config object from the ini file
        config_filename = os.path.join(utils.DROPBOX_ROOT, 'config.ini')
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_filename)

        # iterate over the config to instantiate each person
        self.people = []
        for name, _ in self.config.items('take home pay'):
            self.add_person(name)

        # make sure the data_root exists
        if not os.path.exists(utils.DATA_ROOT):
            os.mkdir(utils.DATA_ROOT)

        # update financial information from quickbooks cache
        self.profit_loss = reports.ProfitLoss()
        self.ar_aging = reports.ARAging()
        self.balance_sheet = reports.BalanceSheet()
        self.unpaid_invoices = reports.UnpaidInvoices()
        self.revenue_projections = reports.RevenueProjections()

        # variables for caching parameters here
        self._monthly_cash = None

    def __iter__(self):
        for person in self.people:
            yield person

    def __len__(self):
        return len(self.people)

    def __getattr__(self, name):
        """This just accesses the value from the config.ini directly"""
        return self.config.getfloat('parameters', name)

    def add_person(self, name):
        person = Person(self, name)
        self.people.append(person)
        return person

    @property
    def n_people(self):
        return len([person for person in self if person.is_active])

    @property
    def n_partners(self):
        return len([person for person in self if person.is_partner])

    def after_tax_target_profit(self):
        """Based on everyone's personal take-home pay goals in config.ini,
        determine the target profit for datascope after taxes
        """

        # estimate how much profit datascope would have to make so that each
        # person's personal goals are satisfied
        personal_after_tax_target_profits = []
        for person in self:
            personal_after_tax_target_profits.append(
                person.after_tax_target_salary_from_bonus_dividends() /
                person.net_fraction_of_profits()
            )

        # if we take the maximum here, then everyone is guaranteed to make *at
        # least* their target take home pay. The median approach makes sure at
        # least half of everyone at datascope meets their personal target take
        # home pay goals.
        return numpy.median(personal_after_tax_target_profits)
        # return max(personal_after_tax_target_profits)

    def before_tax_profit(self):
        # partners must pay taxes at tax_rate, so we need to make
        # 1/(1-tax_rate) more money to account for this
        profit = self.after_tax_target_profit() / (1 - self.tax_rate)

        # partners also pay taxes on their guaranteed payments
        guaranteed_payment = self.after_tax_salary / (1 - self.tax_rate)
        guaranteed_payment_tax = guaranteed_payment * self.tax_rate
        profit += self.n_partners * guaranteed_payment_tax
        return profit

    def revenue(self):
        """Monthly revenue target to accomplish target after-tax take-home pay
        """
        return self.costs() + self.before_tax_profit()

    def costs(self):
        """Estimate rough monthly costs for Datascope"""
        return self.fixed_monthly_costs + \
            self.per_datascoper_costs * self.n_people

    def ebit(self):
        """earnings before interest and taxes (a.k.a. before tax profit
        rate)"""
        return (self.revenue() - self.costs()) / self.revenue()

    def revenue_per_person(self):
        """Annual revenue per person to meet revenue targets"""
        return self.revenue() * 12 / self.n_people

    def minimum_hourly_rate(self):
        """This is the minimum hourly rate necessary to meet our revenue
        targets for the year, without growing.
        """
        yearly_revenue = self.revenue() * 12
        yearly_billable_hours = self.billable_hours_per_year * self.n_people
        return yearly_revenue / yearly_billable_hours

    def iter_future_months(self, n_months):
        # can use any report for this. happened to choose unpaid invoices
        for month in range(1, n_months+1):
            yield self.unpaid_invoices.get_date_in_n_months(month)

    def _get_months_from_now(self, date):
        # can use any report for this. happened to choose unpaid invoices
        return self.unpaid_invoices.get_months_from_now(date)

    @read_or_run
    def simulate_revenues(self, universe, n_months):
        """
        Simulate revenues from accounts receivable data.
        """
        # TODO: Add in revenue from the 'Finalize (SOW/Legal)' Trello list
        # TODO: add in revenue from the 'Proposal Process' Trello list
        # TODO: do some analysis to come up with a good delta_months parameter

        revenues = [0.0] * n_months

        def ontime_noise():
            """Clients rarely pay early and tend to pay late"""
            # TODO: can measure this and make it a not crappy model
            return random.randint(0, 3)

        def work_completion_noise():
            """The end of projects can sometimes drag on a bit, delaying
            payment.
            """
            # TODO: could probably measure this from project planning doodie
            return random.randint(0, 2)

        # revenue from accounts receiveable is, all things considered,
        # extremely certain. The biggest question here is whether people will
        # pay on time.
        for date, balance in self.unpaid_invoices:
            months_from_now = self._get_months_from_now(date)

            # we are presumably actively bugging people about overdue invoices,
            # so these should be paid relatively soon
            months_from_now = max(0, months_from_now)

            # add this balance to the revenues if the revenue hits in the
            # simulation time window
            month = months_from_now + ontime_noise()
            if month < n_months:
                revenues[month] += balance

        # revenue from projects in progress is also relatively certain. There
        # are two sources of variability: (i) whether the work is deemed done
        # in time to receive payment by the specified date and (ii) whether our
        # clients pay on time.
        for date, balance in self.revenue_projections:
            months_from_now = self._get_months_from_now(date)
            month = months_from_now + work_completion_noise() + ontime_noise()
            if month < n_months:
                revenues[month] += balance

        return revenues

# #    @run_or_cache
#     def simulate_costs(self, universe, n_months, n_people):
#         """Simulate datascope's costs over time
#         """
#
#         # get fixed costs from P&L
#         costs = [self.profit_loss.get_fixed_cost()] * n_months
#
#         # get historical cost per person from P&L
#         costs_per_person = self.profit_loss.get_variable_costs_per_person()
#
#         for month, date in enumerate(self.iter_future_months(n_months)):
#
#             # account for quarterly tax draws
#             #
#             # NOTE: this means that we have to have simulated revenues
#             # incorporated into cash expectations
#             if date.month in [1, 4, 6, 9]:
#                 profit = self.calculate_ytd_profit(end_of_previous_quarter)
#                 costs[month] += self.tax_rate * profit
#
#             # 401k contributions
#             #
#             # TODO: also need to even up partner safe harbor contributions
#             # (shouldn't be more than a couple thousand)
#             if date.month == 12:
#                 costs[month] += n_people * 10000
#
#             # TODO: account for annual bonus
#             if date.month == 1:
#                 costs[month] += bonus
#
#         return costs

    def _simulate_single_universe_monthly_cash(self, universe, n_months):
        cash = self.balance_sheet.get_current_cash_in_bank()
        revenues = self.simulate_revenues(universe, n_months)
        # costs = self.simulate_costs(universe, n_months, self.n_people())
        monthly_cash = []
        for month in range(n_months):
            cash -= self.costs()
            if cash < -self.line_of_credit:
                break
            cash += revenues[month]
            monthly_cash.append(cash)
        return monthly_cash

    def simulate_monthly_cash(self, n_months=12, n_universes=1000,
                              verbose=False):
        """Simulate finances and the cash in the bank at the end of every
        month.
        """
        monthly_cash_outputs = []
        for universe in range(n_universes):
            if verbose and universe % 100 == 0:
                print >> sys.stderr, "simulation %d" % universe
            monthly_cash_outputs.append(
                self._simulate_single_universe_monthly_cash(universe, n_months)
            )
        return monthly_cash_outputs

    def get_cash_goal_in_month(self, month):
        """calculate the cash we want to have in the bank in `month` months
        from now
        """
        cash_goal = self.n_months_buffer * self.costs()
        date = utils.date_in_n_months(month)
        cash_goal += date.month * self.after_tax_target_profit()
        return cash_goal

    def get_outcomes_in_month(self, month, monthly_cash_outcomes):
        cash_goal = self.get_cash_goal_in_month(month)
        keys = ['goal', 'buffer', 'no bonus', 'squeak by', 'bye bye']
        outcomes = collections.OrderedDict.fromkeys(keys, 0.0)
        cash_buffer = self.n_months_buffer * self.costs()
        for monthly_cash in monthly_cash_outcomes:
            cash = monthly_cash[month]
            if cash > cash_goal:
                outcomes['goal'] += 1
            elif cash > cash_buffer:
                outcomes['buffer'] += 1
            elif cash > 0:
                outcomes['no bonus'] += 1
            elif cash > -self.line_of_credit:
                outcomes['squeak by'] += 1
            else:
                outcomes['bye bye'] += 1
        norm = sum(outcomes.values())
        if norm > 0:
            for k, v in outcomes.iteritems():
                outcomes[k] = float(v) / norm
        return outcomes
