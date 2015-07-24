import ConfigParser
import random
import os
import collections
import sys
import json
import time

import numpy
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
import arrow

from person import Person


class Datascope(object):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dropbox_root = os.path.join(project_root, 'Dropbox')
    config_filename = os.path.join(dropbox_root, 'config.ini')
    gdrive_credentials_filename = os.path.join(dropbox_root, 'gdrive.json')
    gdrive_cache_max_age = 60 * 30  # in seconds

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
        return self.config.getfloat('parameters', name)

    def _read_googlesheet(self):
        """Using the gdrive credentials file, access the P&L google sheet and
        read all of the content.

        """
        cache = {}
        cache_filename = os.path.join(self.project_root, '.google.cache')
        if os.path.isfile(cache_filename):
            with open(cache_filename) as stream:
                cache = json.load(stream)

        # if cached result is not too old, read result from cache
        if cache and (time.time() - cache['time']) < self.gdrive_cache_max_age:
            print >> sys.stderr, 'Reading P&L data from cache.'
            result = cache['result']

        # otherwise, get it from the spreadsheet
        else:
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
            result = worksheet.get_all_values()

            # write result to cache
            with open(cache_filename, 'w') as stream:
                json.dump({'time': time.time(), 'result': result}, stream)

        # store entire google sheet as attribute and parse
        self.googlesheet = result
        self._parse_googlesheet()

    def _parse_googlesheet(self):
        """Parse out the relevant information from the P&L spreadsheet."""

        # abbreviation
        sheet = self.googlesheet

        # parse revenue by month
        self.historical_monthly_revenues = []
        self.projected_monthly_revenues = []
        for date_string, income_string in zip(sheet[1], sheet[4])[1:]:
            date = arrow.get(date_string)
            income = self._parse_income_string(income_string)
            if date < arrow.now():
                self.historical_monthly_revenues.append((date, income))
            else:
                self.projected_monthly_revenues.append((date, income))

    def _parse_income_string(self, string):
        """Convert a string from spreadsheet into a float, for example
        "$504,234.12" will become 504234."""

        def good_character(char):
            """Check to see if the character is a valid as part of a number"""
            return char in {'.', '-', '+'} or char.isdigit()

        # filter out bad characters
        cleaned = ''.join(i for i in string if good_character(i))

        # cast to float and return (zero if it's empty)
        if cleaned:
            return float(cleaned)
        else:
            return 0.0

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

    def simulate_revenue(self, months_from_now):
        """Use our projected revenues from the P&L sheet with some added
        noise. The estimates are based on the past two years of
        historical monthly data from the P&L sheet, but scaled
        linearly up to the full amount over the course of a year). For
        example, in the next month, the projection will be;

        `next month projection` + 1/12 * noise
        """
        revenue_projection = \
            self.projected_monthly_revenues[months_from_now][1]
        noise_scale = max(0, min(1, (months_from_now - 2) / 12.0))
        noise = noise_scale * \
            random.choice(self.historical_monthly_revenues[-24:])[1]

        return revenue_projection + noise

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
            for month in range(n_months):
                cash -= self.costs()
                if cash < -self.line_of_credit:
                    is_bankrupt = True
                    break
                elif cash < 0:
                    no_cash = True
                cash += self.simulate_revenue(month)
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
