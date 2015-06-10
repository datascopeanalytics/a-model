import ConfigParser
import random
import os
import collections

import numpy

from person import Person


class Datascope(object):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_filename = os.path.join(project_root, 'config.ini')

    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.config_filename)

        # iterate over the config to instantiate each person
        self.people = []
        for name, _ in self.config.items('take home pay'):
            self.add_person(name)

    def __iter__(self):
        for person in self.people:
            yield person

    def __getattr__(self, name):
        """This just accesses the value from the config.ini directly"""
        if name == 'historical_monthly_revenues':
            val = self.config.get('parameters', name)
            return map(float, val.split(','))
        return self.config.getfloat('parameters', name)

    def add_person(self, name):
        person = Person(self, name)
        self.people.append(person)
        return person

    @property
    def n_people(self):
        return len(self.people)

    @property
    def n_partners(self):
        return len([person for person in self if person.is_partner])

    def after_tax_target_profit(self):
        """Based on everyone's personal take-home pay goals, determine the
        target profit for datascope after taxes
        """
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
        #return max(personal_after_tax_target_profits)

    def before_tax_profit(self):
        # partners must pay taxes at tax_rate, so we need to make
        # 1/(1-tax_rate) more money to account for this
        profit = self.after_tax_target_profit() / (1 - self.tax_rate)

        # partners also pay taxes on their guaranteed payments
        profit += self.n_partners * self.after_tax_salary / (1 - self.tax_rate) * self.tax_rate
        return profit

    def revenue(self):
        """Monthly revenue target to accomplish target after-tax take-home pay
        """
        return self.costs() + self.before_tax_profit()

    def costs(self):
        """Estimate rough monthly costs for Datascope"""
        return self.fixed_monthly_costs + self.per_datascoper_costs * self.n_people

    def ebit(self):
        """earnings before interest and taxes (a.k.a. before tax profit rate)"""
        return (self.revenue() - self.costs()) / self.revenue()

    def revenue_per_person(self):
        """Annual revenue per person to meet revenue targets"""
        return self.revenue() * 12 / self.n_people

    def minimum_hourly_rate(self):
        """This is the minimum hourly rate necessary to meet our revenue
        targets for the year, without growing.
        """
        return self.revenue() * 12 / self.billable_hours_per_year / self.n_people

    def simulate_revenue(self):
        """Use the empirical data to simulate a payday from Datascope's
        historical revenue projections. This is a v :hankey: model that does
        not account for correlations in feast-famine cycles, but hey, you gotta
        start somewhere.
        """
        return random.choice(self.historical_monthly_revenues)

    def simulate_finances(self, n_months=12, n_universes=1000):
        """Simulate finances for datascope to quantify a few significant
        outcomes in what could happen.
        """

        # basically what we want to do is simulate starting with a certain amount in
        # the bank, and getting paid X in any given month.
        outcomes = collections.Counter()
        end_cash = []
        for universe in range(n_universes):
            if universe % 100 == 0:
                print "simulation %d" % universe
            is_bankrupt = False
            no_cash = False

            # this game is a gross over simplification. each month datascope pays its
            # expenses and gets paid at the end of the month. This is a terrifying way
            # to run a business---we have quite a bit more information about the
            # business health than "drawing a random number from a black box". For
            # example, we have a sales pipeline, projects underway, and accounts
            # receivable, all of which give us confidence about the current state of
            # affairs beyond the cash on hand at the end of each month.
            cash = initial_cash = self.n_months_buffer * self.costs()
            for month in range(n_months):
                revenue = self.simulate_revenue()
                cash -= self.costs()
                if cash < -self.line_of_credit:
                    is_bankrupt = True
                elif cash < 0:
                    no_cash = True
                cash += revenue
            end_cash.append(cash)

            # how'd we do this year? if we didn't go bankrupt, are we able to give a
            # bonus? do we have excess profit beyond our target profit so we can grow
            # the business
            profit = cash - initial_cash
            if is_bankrupt:
                outcomes['bankrupt'] += 1
            elif no_cash:
                outcomes['survived with line of credit'] += 1
            else:
                outcomes['not bankrupt'] += 1
                if profit < 0:
                    outcomes['no bonus'] += 1
                if profit > 0:
                    outcomes['is bonus'] += 1
                if profit > n_months * self.before_tax_profit():
                    outcomes['can grow business'] += 1

        return outcomes, end_cash
