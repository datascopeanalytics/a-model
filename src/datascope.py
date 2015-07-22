import ConfigParser
import random
import os
import collections
import sys
import json

import numpy
import gspread
from oauth2client.client import SignedJwtAssertionCredentials

from person import Person


class Datascope(object):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dropbox_root = os.path.join(project_root, 'Dropbox')
    config_filename = os.path.join(dropbox_root, 'config.ini')
    gdrive_credentials_filename = os.path.join(dropbox_root, 'gdrive.json')

    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.config_filename)

        # iterate over the config to instantiate each person
        self.people = []
        for name, _ in self.config.items('take home pay'):
            self.add_person(name)

        self._read_googlesheet()
            
    def __iter__(self):
        for person in self.people:
            yield person

    def __getattr__(self, name):
        """This just accesses the value from the config.ini directly"""
        if name == 'historical_monthly_revenues':
            val = self.config.get('parameters', name)
            return map(float, val.split(','))
        return self.config.getfloat('parameters', name)

    def _read_googlesheet(self):
        """Using the gdrive credentials file, access the P&L google sheet and
        read all of the content.

        """
        # read json from file
        with open(self.gdrive_credentials_filename) as stream:
            key = json.load(stream)

        # authorize with credentials
        credentials = SignedJwtAssertionCredentials(
            key['client_email'],
            key['private_key'],
            ['https://spreadsheets.google.com/feeds'],
        )
        gdrive = gspread.authorize(credentials)

        # open spreadsheet and read all content as a list of lists
        spreadsheet = gdrive.open_by_url(key['url'])
        worksheet = spreadsheet.get_worksheet(0)
        self.googlesheet = worksheet.get_all_values()

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

    def simulate_finances(self, n_months=12, n_universes=1000,
        initial_cash=None, verbose=False):
        """Simulate finances for datascope to quantify a few significant
        outcomes in what could happen.
        """

        # assume we're starting out with our full buffer if nothing is specified
        cash_buffer = self.n_months_buffer * self.costs()
        if initial_cash is None:
            initial_cash = cash_buffer

        # basically what we want to do is simulate starting with a certain amount in
        # the bank, and getting paid X in any given month.
        outcomes = collections.Counter()
        end_cash = []
        for universe in range(n_universes):
            if verbose and universe % 100 == 0:
                print >> sys.stderr, "simulation %d" % universe
            is_bankrupt = False
            no_cash = False

            # this game is a gross over simplification. each month datascope pays its
            # expenses and gets paid at the end of the month. This is a terrifying way
            # to run a business---we have quite a bit more information about the
            # business health than "drawing a random number from a black box". For
            # example, we have a sales pipeline, projects underway, and accounts
            # receivable, all of which give us confidence about the current state of
            # affairs beyond the cash on hand at the end of each month.
            cash = initial_cash
            for month in range(n_months):
                cash -= self.costs()
                if cash < -self.line_of_credit:
                    is_bankrupt = True
                    break
                elif cash < 0:
                    no_cash = True
                cash += self.simulate_revenue()
            end_cash.append(cash)

            # how'd we do this year? if we didn't go bankrupt, are we able to give a
            # bonus? do we have excess profit beyond our target profit so we can grow
            # the business
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
