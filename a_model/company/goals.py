import datetime

import numpy
import collections
import scipy.optimize

from .. import utils


class GoalCompanyMixin(object):
    """This Mixin holds all of the functionality related to calculating the
    financial goals of the Company.
    """

    def get_cash_goal(self, date):
        annual_cash_goal = dict(self.get_annual_cash_goal(date.year))
        return annual_cash_goal[date]

    def get_annual_cash_goal(self, year):
        """do a goal seek to figure out how much revenue per datascoper per
        month we need to generate to meet our goal profitability
        """
        if not hasattr(self, '_annual_cash_goals'):
            self._annual_cash_goals = {}
        if year in self._annual_cash_goals:
            return self._annual_cash_goals[year]
        t0 = utils.end_of_month(
            datetime.date(year, 1, 1)
        )
        t1 = datetime.date(year, 12, 31)
        cash0 = self.get_cash_buffer(t0)
        average_tax_rate = self.average_tax_rate(t1)

        # average number of people
        n_average, n = 0.0, 0.0
        for t in utils.iter_end_of_months(t0, t1):
            n_average += self.n_people(t)
            n += 1.0
        n_average /= n

        # costs are fixed for the year by the number of people
        def constant_costs():
            costs = []
            fixed_cost = self.profit_loss.get_average_fixed_cost()
            per_person_cost = numpy.mean(
                self.get_historical_per_person_costs()
            )
            for t in utils.iter_end_of_months(t0, t1):
                n = self.n_people(t)
                costs.append(fixed_cost + n * per_person_cost)
            costs[-1] += self.get_401k_contribution(t1)
            return costs

        def constant_revenues(monthly_revenue_per_person):
            revenues = []
            for t in utils.iter_end_of_months(t0, t1):
                n = self.n_people(t)
                revenues.append(n * monthly_revenue_per_person)
            return revenues

        def helper(monthly_revenue_per_person):
            # fit the eoy cash to be the same as the cash buffer. square the
            # result to make sure the numer is positive for optimization
            # purposes
            revenues = constant_revenues(monthly_revenue_per_person)
            costs = constant_costs()
            monthly_cash, bonus_pool, quarterly_taxes = self.get_monthly_cash(
                t0, revenues, costs, cash=cash0,
                ytd_revenue=0.0, ytd_cost=0.0, ytd_tax_draws=0.0,
            )
            a = monthly_cash[-1] - self.get_cash_buffer(t1)

            # calculate the target bonus pool size and make sure the actual
            # bonus pool is close
            monthly_salary = self.before_tax_annual_salary / 12.0
            target_bonus = monthly_salary * self.n_months_before_tax_bonus
            target_bonus_pool = n_average * target_bonus / \
                (1.0 - self.fraction_profit_for_dividends)
            b = bonus_pool - target_bonus_pool

            # TODO: does this do the correct thing with Q4 taxes in january
            # print monthly_revenue_per_person, bonus_pool, target_pool, a, b
            return b * b

        # optimize the function above to find the amount of revenue per person
        # per month that is necessary to meet our target
        # http://bit.ly/1q5XNE8
        opt = scipy.optimize.minimize_scalar(
            helper,
            bounds=(5000, 30000),
            method='bounded',
        )

        # get the cash goal by simulating this idealized revenue stream. be
        # sure to add back the bonus pool to December in the monthly cash so
        # that other calculations work correctly
        revenues = constant_revenues(opt.x)
        costs = constant_costs()
        monthly_cash, bonus_pool, quarterly_taxes = self.get_monthly_cash(
            t0, revenues, costs, cash=cash0,
            ytd_revenue=0.0, ytd_cost=0.0, ytd_tax_draws=0.0,
        )
        monthly_cash[-1] += bonus_pool
        result = [(datetime.date(t0.year, t0.month, 1), cash0)]
        self._annual_cash_goals[year] = result
        for t, cash in zip(utils.iter_end_of_months(t0, t1), monthly_cash):
            result.append((t, cash))
        result.append((
            t1 + datetime.timedelta(days=1),
            monthly_cash[-1]-bonus_pool,
        ))

        # print out some helpful statistics
        r = sum(revenues)
        print "TARGET %d REVENUES" % year, utils.currency_str(r)
        print "...THAT's %s PER PERSON" % utils.currency_str(r / n_average)

        return result

    def get_outcomes_in_month(self, month, monthly_cash_outcomes):
        date = utils.date_in_n_months(month)
        cash_goal = self.get_cash_goal(date)
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
            elif cash >= cash_buffer:
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
