import ConfigParser
import random
import os
import collections
import sys
import json
import time
import datetime

import numpy

from person import Person
import utils
import reports


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

    def __iter__(self):
        for person in self.people:
            yield person

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

    def simulate_revenues(self, n_months):
        """
        Simulate revenues from accounts receivable data.

        TODO:
        * Add in projected revenue from signed projects from google spreadsheet
        * Add in revenue from the 'Finalize (SOW/Legal)' Trello list
        * add in revenue from the 'Proposal Process' Trello list
        * do some analysis to come up with a good `delta_months` parameter
        """
        revenues = [0.0] * n_months
        now = utils.end_of_last_month()
        delta_months = 3
        for date, balance in self.unpaid_invoices:

            # we are presumably actively bugging people about overdue invoices,
            # so these should be paid sometime over the next three months
            if date < now:
                month = random.randint(0, delta_months-1)

            # for invoices that are not yet overdue, they should be paid within
            # delta_months time (if not *on time*)
            else:
                delta = date - now
                months_from_now = int(round(delta.days / 30.))
                month = months_from_now + random.randint(0, delta_months-1)

            # add this balance to the revenues if the revenue hits in the
            # simulation time window
            if month < n_months:
                revenues[month] += balance

        return revenues

    def simulate_finances(self, n_months=12, n_universes=1000,
                          initial_cash=None, verbose=False):
        """Simulate finances for datascope to quantify a few significant
        outcomes in what could happen.
        """
        # assume we're starting out with our full buffer if nothing is
        # specified
        cash_buffer = self.n_months_buffer * self.costs()
        if initial_cash is None:
            initial_cash = cash_buffer

        # basically what we want to do is simulate starting with a
        # certain amount in the bank, and getting paid X in any given
        # month.
        outcomes = collections.Counter()
        end_cash = []
        for universe in range(n_universes):
            if verbose and universe % 100 == 0:
                print >> sys.stderr, "simulation %d" % universe
            is_bankrupt = False
            no_cash = False

            # this game is a gross over simplification. each month
            # datascope pays its expenses and gets paid at the end of
            # the month. This is a terrifying way to run a
            # business---we have quite a bit more information about
            # the business health than "drawing a random number from a
            # black box". For example, we have a sales pipeline,
            # projects underway, and accounts receivable, all of which
            # give us confidence about the current state of affairs
            # beyond the cash on hand at the end of each month.
            cash = initial_cash
            revenues = self.simulate_revenues(n_months)
            for month in range(n_months):
                cash -= self.costs()
                if cash < -self.line_of_credit:
                    is_bankrupt = True
                    break
                elif cash < 0:
                    no_cash = True
                cash += revenues[month]
            end_cash.append(cash)

            # how'd we do this year? if we didn't go bankrupt, are we
            # able to give a bonus? do we have excess profit beyond
            # our target profit so we can grow the business
            profit = cash - cash_buffer
            if is_bankrupt:
                outcomes['bankrupt'] += 1
                outcomes['no bonus'] += 1
            else:
                outcomes['not bankrupt'] += 1
                if no_cash:
                    outcomes['survived with line of credit'] += 1
                if profit < 0:
                    outcomes['no bonus'] += 1
                if profit > 0:
                    outcomes['is bonus'] += 1
                if profit > n_months * self.before_tax_profit():
                    outcomes['can grow business'] += 1

        return outcomes, end_cash
