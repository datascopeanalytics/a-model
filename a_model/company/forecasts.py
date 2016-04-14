import random
import collections

from dateutil.relativedelta import relativedelta
import numpy


class ForecastCompanyMixin(object):
    """This Mixin holds everything related to forecasting cashflow into the
    future"""

    # @read_or_run
    def simulate_revenues(self, universe, n_months, **kwargs):
        """Simulate revenues from accounts receivable data.
        """
        # TODO: Add in revenue from the 'Finalize (SOW/Legal)' Trello list
        # TODO: add in revenue from the 'Proposal Process' Trello list
        # TODO: do some analysis to come up with a good delta_months parameter

        revenues = [0.0] * n_months

        def ontime_payment_noise():
            """Clients rarely pay early and tend to pay late"""
            # TODO: can measure this and make it a not crappy model
            if kwargs.get('ontime_payment', False):
                return 0
            return random.randint(0, 2)

        def ontime_completion_noise():
            """The end of projects can sometimes drag on a bit, delaying
            payment.
            """
            # TODO: could probably measure this from project planning doodie
            if kwargs.get('ontime_completion', False):
                return 0
            return random.randint(0, 2)

        def payment_terms():
            # TODO: could probably get this from quickbooks some how, or
            # perhaps we could infer this from the due date on invoices?
            return 1

        # revenue from accounts receiveable is, all things considered,
        # extremely certain. The biggest question here is whether people will
        # pay on time.
        for date, balance in self.unpaid_invoices:
            months_from_now = self._get_months_from_now(date) - 1

            # we are presumably actively bugging people about overdue invoices,
            # so these should be paid relatively soon
            months_from_now = max(0, months_from_now)

            # add this balance to the revenues if the revenue hits in the
            # simulation time window
            month = months_from_now + ontime_payment_noise()
            if month < n_months:
                revenues[month] += balance

        # revenue from projects in progress is also relatively certain. There
        # are two sources of variability: (i) whether the work is deemed done
        # in time to receive payment by the specified date and (ii) whether our
        # clients pay on time.
        for date, balance in self.invoice_projections:
            months_from_now = self._get_months_from_now(date)
            month = months_from_now + payment_terms() + \
                ontime_completion_noise() + ontime_payment_noise()
            if month < n_months:
                revenues[month] += balance
        return revenues

#    @run_or_cache
    def simulate_costs(self, universe, n_months, **kwargs):
        """Simulate datascope's costs over time
        """

        # get fixed costs from P&L and treat it like a constant. only use the
        # last 12 months of historical per-person costs to better calibrate for
        # recent changes in expenses.
        fixed_cost = self.profit_loss.get_average_fixed_cost()
        per_person_costs = self.get_historical_per_person_costs()[-12:]

        # variable costs (i) scale with the number of people and (ii) vary
        # quite a bit more.
        def variable_cost(n_people):
            return n_people * random.choice(per_person_costs)

        costs = [0.0] * n_months
        for month, date in enumerate(self.iter_future_months(n_months)):
            n_people = self.n_people(date)
            costs[month] += fixed_cost + variable_cost(n_people)

            # handle big, consistently timed expenses here
            if date.month == 12:
                costs[month] += self.get_401k_contribution(date)
        return costs

    def get_monthly_cash(self, start_date, revenues, costs, cash=None,
                         ytd_revenue=None, ytd_cost=None, ytd_tax_draws=None):
        """This function takes some predefined revenues, costs, and any other
        relevant financial information and computes the monthly_cash
        """
        assert len(revenues) == len(costs)
        if cash is None:
            cash = self.balance_sheet.get_current_cash_in_bank()
        if ytd_revenue is None:
            ytd_revenue = self.profit_loss.get_ytd_revenue()
        if ytd_cost is None:
            ytd_cost = self.profit_loss.get_ytd_cost()

        # TODO get Lyuda / Matt to help us have a quickbooks report that makes
        # it easy to get this information directly from quickbooks instead of
        # having to enter it by hand in the config.ini
        if ytd_tax_draws is None:
            ytd_tax_draws = self.ytd_tax_draws
        tax_months = set([1, 4, 6, 9])
        quarterly_taxes = dict((month, None) for month in tax_months)
        monthly_cash = []
        bonus_pool = None
        for month in range(len(revenues)):
            date = start_date + relativedelta(months=month)

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

            # pay bonuses at the end of December. can instead count this in
            # January if it looks like Datascope's profits will grow in the
            # next year, but this gives us the flexibility to pay bonuses early
            # if appropriate. bonus calculation has to happen here to have
            # access to the net cash in the bank at the end of the month. bonus
            # counts as an expense and reduces our tax burden. taxes have
            # already been paid on dividends and are just drawn from the bank.
            if date.month == 12:
                # TODO: this currently calculates things in a very conservative
                # way by calculating taxes BEFORE calculating the bonus. half
                # of the bonus_pool counts as a cost for the business, which
                # would reduce our Q4 tax burden if we actually pay bonuses in
                # december.
                #
                # TODO: have command line option to do bonuses after the new
                # year
                _ytd_revenue = ytd_revenue + revenues[month]
                _ytd_cost = ytd_cost + costs[month]
                _ytd_profit = max([0.0, _ytd_revenue - _ytd_cost])
                q4_tax = self.tax_rate * _ytd_profit - ytd_tax_draws
                q4_tax = max([0.0, q4_tax])
                eom_cash = cash + revenues[month] - costs[month] - q4_tax
                buffer = self.get_cash_buffer(date)
                bonus_pool = max([0.0, eom_cash - buffer])
                f = self.fraction_profit_for_dividends
                costs[month] += (1.0 - f) * bonus_pool
                cash -= f * bonus_pool

            # pay all normal expenses and add revenues for the month
            cash -= costs[month]
            cash += revenues[month]
            ytd_cost += costs[month]
            ytd_revenue += revenues[month]

            # reset the ytd calculations as necessary to make the tax
            # calculations correct
            if date.month == 12:
                ytd_revenue, ytd_cost = 0.0, 0.0
                ytd_tax_draws = 0.0

            # record and return the cash in the bank at the end of the month
            monthly_cash.append(cash)

        return monthly_cash, bonus_pool, quarterly_taxes

    def _simulate_single_universe_monthly_cash(self, universe, n_months,
                                               **kwargs):
        for start_date in self.iter_future_months(1):
            pass
        return self.get_monthly_cash(
           start_date,
           self.simulate_revenues(universe, n_months, **kwargs),
           self.simulate_costs(universe, n_months, **kwargs),
        )

    def simulate_monthly_cash(self, n_months=12, n_universes=1000,
                              verbose=False, **kwargs):
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
                self._simulate_single_universe_monthly_cash(
                    universe, n_months, **kwargs
                )
            monthly_cash_outputs.append(monthly_cash)
            bonus_pool_outputs.append(bonus_pool)
            for month in quarterly_taxes:
                quarterly_tax_outputs[month].append(quarterly_taxes[month])
        return monthly_cash_outputs, bonus_pool_outputs, quarterly_tax_outputs
