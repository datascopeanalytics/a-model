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

    def __init__(self, today=None):

        # instantiate the config object from the ini file
        config_filename = os.path.join(utils.DROPBOX_ROOT, 'config.ini')
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_filename)

        # make sure the data_root exists
        if not os.path.exists(utils.DATA_ROOT):
            os.mkdir(utils.DATA_ROOT)

        # create datascope as if it were created today
        self.today = today or datetime.date.today()

        # update financial information from quickbooks cache
        self.profit_loss = reports.ProfitLoss(self.today)
        self.ar_aging = reports.ARAging(self.today)
        self.balance_sheet = reports.BalanceSheet(self.today)
        self.unpaid_invoices = reports.UnpaidInvoices(self.today)
        self.revenue_projections = reports.RevenueProjections(self.today)
        self.roster = reports.Roster(self.today)

        # iterate over the config to instantiate each person
        self.people = []
        for person in self.roster.iter_people():
            self.add_person(person)

        # variables for caching parameters here
        self._monthly_cash = None

    def iter_people(self, date=None):
        """iterate over all people present at Datascope on `date`."""
        for person in self.people:
            if date is None or person.is_active(date):
                yield person

    def __len__(self):
        return len(self.people)

    def __getattr__(self, name):
        """This just accesses the value from the config.ini directly"""
        return self.config.getfloat('parameters', name)

    def add_person(self, person_or_name, *args, **kwargs):
        if isinstance(person_or_name, Person):
            person = person_or_name
            person.datascope = self
        else:
            person = Person(self, person_or_name, *args, **kwargs)
        self.people.append(person)
        return person

    def n_people(self, date):
        """number of people that are active datascopers"""
        return len([person for person in self.iter_people(date)])

    def n_partners(self, date):
        return len([person for person in self.iter_people()
                    if person.is_partner(date)])

    def after_tax_target_profit(self, date):
        """Based on everyone's personal take-home pay goals in config.ini,
        determine the target profit for datascope after taxes
        """

        # estimate how much profit datascope would have to make so that each
        # person's personal goals are satisfied
        personal_after_tax_target_profits = []
        for person in self.iter_people(date):
            personal_after_tax_target_profits.append(
                person.after_tax_target_salary_from_bonus_dividends() /
                person.net_fraction_of_profits(date)
            )

        # if we take the maximum here, then everyone is guaranteed to make *at
        # least* their target take home pay. The median approach makes sure at
        # least half of everyone at datascope meets their personal target take
        # home pay goals.
        return numpy.median(personal_after_tax_target_profits)
        # return max(personal_after_tax_target_profits)

    def before_tax_target_profit(self, date):
        # partners must pay taxes at tax_rate, so we need to make
        # 1/(1-tax_rate) more money to account for this
        profit = self.after_tax_target_profit(date) / (1 - self.tax_rate)

        # partners also pay taxes on their guaranteed payments
        guaranteed_payment = self.after_tax_salary / (1 - self.tax_rate)
        guaranteed_payment_tax = guaranteed_payment * self.tax_rate
        profit += self.n_partners(date) * guaranteed_payment_tax
        return profit

    def revenue(self, date):
        """Monthly revenue target to accomplish target after-tax take-home pay
        """
        return self.average_historical_costs() + \
            self.before_tax_target_profit(date)

    def average_historical_costs(self):
        """Estimate rough monthly costs for Datascope"""
        _, costs = zip(*self.profit_loss.get_historical_costs())
        return sum(costs) / len(costs)

    def ebit(self, date):
        """earnings before interest and taxes (a.k.a. before tax profit
        rate)"""
        revenue = self.revenue(date)
        cost = self.average_historical_costs()
        return (revenue - cost) / revenue

    def revenue_per_person(self, date):
        """Annual revenue per person to meet revenue targets"""
        return self.revenue(date) * 12 / self.n_people(date)

    def minimum_hourly_rate(self, date):
        """This is the minimum hourly rate necessary to meet our revenue
        targets for the year, without growing.
        """
        yearly_revenue = self.revenue(date) * 12
        yearly_billable_hours = self.billable_hours_per_year * \
            self.n_people(date)
        return yearly_revenue / yearly_billable_hours

    def get_cash_buffer(self, date=None):
        """get the cash buffer. without a specific `date` to calculate the
        number of people, just assume the overall average historical cost
        """
        if date is None:
            cost = self.average_historical_costs()
        else:
            n_people = self.n_people(date)
            fixed_cost = self.profit_loss.get_average_fixed_cost()
            per_person_costs = \
                self.profit_loss.get_historical_per_person_costs()
            per_person_cost = sum(per_person_costs) / len(per_person_costs)
            cost = fixed_cost + n_people * per_person_cost
        return self.n_months_buffer * cost

    def iter_future_months(self, n_months):
        # can use any report for this. happened to choose unpaid invoices
        for month in range(1, n_months+1):
            yield self.unpaid_invoices.get_date_in_n_months(month)

    def _get_months_from_now(self, date):
        # can use any report for this. happened to choose unpaid invoices
        return self.unpaid_invoices.get_months_from_now(date)

    # @read_or_run
    def simulate_revenues(self, universe, n_months):
        """Simulate revenues from accounts receivable data.
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

#    @run_or_cache
    def simulate_costs(self, universe, n_months):
        """Simulate datascope's costs over time
        """

        # get fixed costs from P&L and treat it like a constant
        fixed_cost = self.profit_loss.get_average_fixed_cost()
        per_person_costs = self.profit_loss.get_historical_per_person_costs()

        # variable costs (i) scale with the number of people and (ii) vary
        # quite a bit more.
        def variable_cost(n_people):
            return n_people * random.choice(per_person_costs)

        costs = [0.0] * n_months
        for month, date in enumerate(self.iter_future_months(n_months)):
            n_people = self.n_people(date)
            costs[month] += fixed_cost + variable_cost(n_people)

            # 401k contributions
            #
            # TODO: also need to even up partner safe harbor contributions
            # (shouldn't be more than a couple thousand)
            if date.month == 12:
                costs[month] += n_people * self.retirement_contribution

        return costs

    def _simulate_single_universe_monthly_cash(self, universe, n_months):
        tax_months = set([1, 4, 6, 9])
        cash = self.balance_sheet.get_current_cash_in_bank()
        ytd_revenue = self.profit_loss.get_ytd_revenue()
        ytd_cost = self.profit_loss.get_ytd_cost()
        # TODO get Lyuda / Matt to help us have a quickbooks report that makes
        # it easy to get this information directly from quickbooks instead of
        # having to enter it by hand in the config.ini
        ytd_tax_draws = self.ytd_tax_draws
        revenues = self.simulate_revenues(universe, n_months)
        costs = self.simulate_costs(universe, n_months)
        monthly_cash = []
        bonus_pool = None
        quarterly_taxes = dict((month, None) for month in tax_months)
        for month, date in enumerate(self.iter_future_months(n_months)):

            # quarterly tax draws only decrease the cash in the bank; they do
            # not count as a cost for datascope. the tax draw in january is for
            # Q4 of the previous year so we reset the ytd_* values below. we
            # pay taxes on our ytd profit but without also paying duplicate
            # taxes on the previous quarters
            if date.month in tax_months:
                ytd_profit = max([0.0, ytd_revenue - ytd_cost])
                quarterly_tax = self.tax_rate * ytd_profit - ytd_tax_draws
                quarterly_tax = max([0.0, quarterly_tax])
                quarterly_taxes[date.month] = quarterly_tax
                cash -= quarterly_tax
                ytd_tax_draws += quarterly_tax

            # pay all normal expenses and add revenues for the month
            cash -= costs[month]
            cash += revenues[month]

            # pay bonuses at the end of December. can instead count this in
            # January if it looks like Datascope's profits will grow in the
            # next year, but this gives us the flexibility to pay bonuses early
            # if appropriate. bonus calculation has to happen here to have
            # access to the net cash in the bank at the end of the month. bonus
            # counts as an expense and reduces our tax burden. taxes have
            # already been paid on dividends and are just drawn from the bank.
            if date.month == 12:
                buffer = self.get_cash_buffer()
                bonus_pool = max([0.0, cash - buffer])
                f = self.fraction_profit_for_dividends
                costs[month] += (1.0 - f) * bonus_pool
                cash -= f * bonus_pool

            # reset the ytd calculations as necessary to make the tax
            # calculations correct
            if date.month == 1:
                ytd_revenue, ytd_cost = 0.0, 0.0
                ytd_tax_draws = 0.0
            ytd_cost += costs[month]
            ytd_revenue += revenues[month]

            # record and return the cash in the bank at the end of the month
            monthly_cash.append(cash)
        return monthly_cash, bonus_pool, quarterly_taxes

    def simulate_monthly_cash(self, n_months=12, n_universes=1000,
                              verbose=False):
        """Simulate finances and the cash in the bank at the end of every
        month.
        """
        monthly_cash_outputs = []
        bonus_pool_outputs = []
        quarterly_tax_outputs = collections.defaultdict(list)
        for universe in range(n_universes):
            if verbose and universe % 100 == 0:
                print >> sys.stderr, "simulation %d" % universe
            monthly_cash, bonus_pool, quarterly_taxes = \
                self._simulate_single_universe_monthly_cash(universe, n_months)
            monthly_cash_outputs.append(monthly_cash)
            bonus_pool_outputs.append(bonus_pool)
            for month in quarterly_taxes:
                quarterly_tax_outputs[month].append(quarterly_taxes[month])
        return monthly_cash_outputs, bonus_pool_outputs, quarterly_tax_outputs

    def get_cash_goal_in_month(self, month):
        """calculate the cash we want to have in the bank in `month` months
        from now
        """
        cash_goal = self.n_months_buffer * self.average_historical_costs()
        date = utils.date_in_n_months(month)
        cash_goal += date.month * self.after_tax_target_profit(date)
        return cash_goal

    def get_outcomes_in_month(self, month, monthly_cash_outcomes):
        date = utils.date_in_n_months(month)
        cash_goal = self.get_cash_goal_in_month(month)
        keys = [
            '>goal bonus',
            'buffer+bonus',
            'buffer low,\n no bonus',
            'dip into credit',
            'bye bye',
        ]
        outcomes = collections.OrderedDict.fromkeys(keys, 0.0)
        cash_buffer = self.get_cash_buffer(date)
        for i in range(len(monthly_cash_outcomes)):
            monthly_cash = monthly_cash_outcomes[i]
            cash = monthly_cash[month-1]
            # TODO: do we need to use the bonus_pool_outcomes to properly
            # estimate things?
            if cash > cash_goal:
                outcomes[keys[0]] += 1
            elif cash > cash_buffer:
                outcomes[keys[1]] += 1
            elif cash > 0:
                outcomes[keys[2]] += 1
            elif cash > -self.line_of_credit:
                outcomes[keys[3]] += 1
            else:
                outcomes[keys[4]] += 1
        norm = sum(outcomes.values())
        if norm > 0:
            for k, v in outcomes.iteritems():
                outcomes[k] = float(v) / norm
        return outcomes
