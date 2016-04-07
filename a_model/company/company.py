import os
import ConfigParser
import datetime

from .. import reports


class BaseCompany(object):
    """The company class is the base class that is used to manage people,
    financial reports, and to calculate basic financials.
    """

    def __init__(self, today=None, add_people=True):

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
        self.invoice_projections = reports.InvoiceProjections(self.today)
        self.roster = reports.Roster(self.today)

        # iterate over the config to instantiate each person
        self.people = []
        if add_people:
            for person in self.roster.iter_people():
                self.add_person(person)

        # variables for caching parameters here
        self._monthly_cash = None

    def __getattr__(self, name):
        """This just accesses the value from the config.ini directly"""
        return self.config.getfloat('parameters', name)

    ############################################################ MANAGE PEOPLE
    def add_person(self, person_or_name, *args, **kwargs):
        if isinstance(person_or_name, Person):
            person = person_or_name
            person.datascope = self
        else:
            person = Person(self, person_or_name, *args, **kwargs)
        self.people.append(person)
        return person

    def iter_people(self, date=None):
        """iterate over all people present at Datascope on `date`."""
        for person in self.people:
            if date is None or person.is_active_or_partner(date):
                yield person

    def __len__(self):
        return len(self.people)

    def n_people(self, date):
        """number of people that are active datascopers"""
        return len([person for person in self.iter_people(date)])

    def n_partners(self, date):
        return len([person for person in self.iter_people()
                    if person.is_partner(date)])

    ######################################################### BASIC FINANCIALS
    def average_historical_costs(self):
        """Estimate rough monthly costs for Datascope"""
        _, costs = zip(*self.profit_loss.get_historical_costs())
        return sum(costs) / len(costs)

    def get_historical_per_person_costs(self):
        """Get the historical per-person costs after removing things like fixed
        costs (see `ProfitLoss.get_historical_fixed_costs` for details) and
        401(k) contributions

        TODO: this should also omit bonuses as those are accounted for in
        Company._simulate_single_universe_monthly_cash
        """

        # calculate the variable cost
        historical_costs = self.profit_loss.get_historical_costs()
        dates, costs = zip(*historical_costs)
        fixed_costs = self.profit_loss.get_historical_fixed_costs()
        retirement_costs = self.profit_loss.get_historical_retirement_costs()
        _, retirement_costs = zip(*retirement_costs)
        iterator = zip(dates, costs, fixed_costs, retirement_costs)
        variable_costs = []
        for date, cost, fixed_cost, retirement_cost in iterator:
            # TODO: this should also omit bonuses and old-style tax payments as
            # those are accounted for elsewhere
            variable_costs.append((date, cost - fixed_cost - retirement_cost))
        historical_per_person_costs = []
        for date, variable_cost in variable_costs:
            per_person_cost = variable_cost / self.n_people(date)
            historical_per_person_costs.append(per_person_cost)
        return historical_per_person_costs

    def revenue(self, date):
        """Monthly revenue target to accomplish target after-tax take-home pay
        """
        raise NotImplementedError(
            'should calculate this as of this particular `date`'
        )
        return self.average_historical_costs() + \
            self.before_tax_target_profit(date)

    def ebit(self, date):
        """earnings before interest and taxes (a.k.a. before tax profit
        rate)"""
        raise NotImplementedError(
            'should calculate this as of this particular `date`'
        )
        revenue = self.revenue(date)
        cost = self.average_historical_costs()
        return (revenue - cost) / revenue

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
                self.get_historical_per_person_costs()
            per_person_cost = sum(per_person_costs) / len(per_person_costs)
            cost = fixed_cost + n_people * per_person_cost
        return self.n_months_buffer * cost

    ######################################################## TODO: REFACTOR ME
    def iter_future_months(self, n_months):
        # can use any report for this. happened to choose unpaid invoices
        for month in range(1, n_months+1):
            yield self.unpaid_invoices.get_date_in_n_months(month)

    def _get_months_from_now(self, date):
        # can use any report for this. happened to choose unpaid invoices
        return self.unpaid_invoices.get_months_from_now(date)
