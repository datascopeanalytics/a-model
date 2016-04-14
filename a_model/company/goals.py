import datetime

import numpy
import collections
import scipy.optimize

from .. import utils


class GoalCompanyMixin(object):
    """This Mixin holds all of the functionality related to calculating the
    financial goals of the Company.
    """

    def get_cash_goal(self):
        """do a goal seek to figure out how much revenue per datascoper per
        month we need to generate to meet our goal profitability
        """
        t0 = utils.end_of_month(
            datetime.date(datetime.date.today().year, 1, 1)
        )
        t1 = datetime.date(datetime.date.today().year, 12, 31)
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

        # get the cash goal by simulating this idealized revenue stream
        revenues = constant_revenues(opt.x)
        costs = constant_costs()
        monthly_cash, bonus_pool, quarterly_taxes = self.get_monthly_cash(
            t0, revenues, costs, cash=cash0,
            ytd_revenue=0.0, ytd_cost=0.0, ytd_tax_draws=0.0,
        )
        result = [(datetime.date(t0.year, t0.month, 1), cash0)]
        for t, cash in zip(utils.iter_end_of_months(t0, t1), monthly_cash):
            result.append((t, cash))
        return result

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

    ########################################################## DEPRICATE THESE
    def get_cash_goal_in_month(self, month):
        """calculate the cash we want to have in the bank in `month` months
        from now
        """
        # TODO: DEPRECATE
        cash_goal = self.n_months_buffer * self.average_historical_costs()
        date = utils.date_in_n_months(month)
        cash_goal += date.month * self.after_tax_target_profit(date)
        return cash_goal

    def after_tax_target_profit(self, date):
        """Based on everyone's personal take-home pay goals in config.ini,
        determine the target profit for datascope after taxes
        """

        # estimate how much profit datascope would have to make so that each
        # person's personal goals are satisfied
        personal_after_tax_target_profits = []
        for person in self.iter_people_and_partners(date):
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
