import os
import ConfigParser

import numpy


class Person(object):
    def __init__(self, datascope, name):
        self.datascope = datascope
        self.name = name

    @property
    def is_partner(self):
        return self.ownership > 0

    @property
    def ownership(self):
        try:
            return self.datascope.config.getfloat('ownership', self.name)
        except ConfigParser.NoOptionError:
            return 0.0

    @property
    def after_tax_target_salary(self):
        """This is on a per month basis, but includes biweekly salary as well
        as annual bonus and dividends. If the target take home pay is not
        specified, then we estimate the target take home pay from the monthly
        after tax pay and the number of months of after tax bonus expected at
        the end of the year.
        """
        pay = self.datascope.config.get('take home pay', self.name)
        try:
            pay = float(pay)
        except ValueError:
            pay = self.datascope.after_tax_salary
            pay *= (1 + self.datascope.n_months_after_tax_bonus/12)
        return pay

    @property
    def net_fraction_of_profits(self):
        return (
            self.datascope.fraction_profit_for_dividends * self.ownership +
            (1.0-self.datascope.fraction_profit_for_dividends) / self.datascope.n_people
        )

    @property
    def after_tax_target_salary_from_bonus_dividends(self):
        return self.after_tax_target_salary - self.datascope.after_tax_salary

    @property
    def after_tax_salary_from_bonus(self):
        return (1.0-self.datascope.fraction_profit_for_dividends) / self.datascope.n_people * self.datascope.after_tax_target_profit

    @property
    def after_tax_salary_from_dividends(self):
        return self.datascope.fraction_profit_for_dividends * self.ownership * self.datascope.after_tax_target_profit

    @property
    def after_tax_salary(self):
        return self.after_tax_salary_from_bonus + self.after_tax_salary_from_dividends + self.datascope.after_tax_salary


class Datascope(object):
    def __init__(self, config_filename):
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_filename)

        # iterate over the config to instantiate each person
        self.people = []
        for name, _ in self.config.items('take home pay'):
            self.people.append(Person(self, name))

    def __iter__(self):
        for person in self.people:
            yield person

    def __getattr__(self, name):
        """This just accesses the value from the config.ini directly"""
        return self.config.getfloat('parameters', name)

    @property
    def n_people(self):
        return len(self.people)

    @property
    def n_partners(self):
        return len([person for person in self if person.is_partner])

    @property
    def after_tax_target_profit(self):
        """
        """
        personal_after_tax_target_profits = []
        for person in self:
            personal_after_tax_target_profits.append(
                person.after_tax_target_salary_from_bonus_dividends /
                person.net_fraction_of_profits
            )

        # if we take the maximum here, then everyone is guaranteed to make *at
        # least* their target take home pay. The median approach makes sure at
        # least half of everyone at datascope meets their personal target take
        # home pay goals.
        return numpy.median(personal_after_tax_target_profits)
        # return max(personal_after_tax_target_profits)

    @property
    def before_tax_profit(self):
        # partners must pay taxes at tax_rate, so we need to make
        # 1/(1-tax_rate) more money to account for this
        profit = self.after_tax_target_profit / (1 - self.tax_rate)

        # partners also pay taxes on their guaranteed payments
        profit += self.n_partners * self.after_tax_salary / (1 - self.tax_rate) * self.tax_rate
        return profit

    @property
    def revenue(self):
        return self.costs + self.before_tax_profit

    @property
    def costs(self):
        return self.fixed_monthly_costs + self.per_datascoper_costs * self.n_people

    @property
    def ebit(self):
        """earnings before interest and taxes (a.k.a. before tax profit rate)"""
        return (self.revenue - self.costs) / self.revenue

    @property
    def revenue_per_person(self):
        return self.revenue * 12 / self.n_people

    @property
    def minimum_hourly_rate(self):
        """This is the minimum hourly rate necessary to meet our revenue
        targets for the year, without growing.
        """
        return self.revenue * 12 / self.billable_hours_per_year / self.n_people

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datascope = Datascope(os.path.join(project_root, 'config.ini'))
    # print datascope.n_people, datascope.n_partners
    # for person in datascope:
    #     print person.name, person.after_tax_target_salary, person.ownership, person.net_fraction_of_profits
    #
    # print "DATASCOPE AFTER TAX TARGET PROFIT"
    # print datascope.after_tax_target_profit


    for person in datascope:
        print person.name, person.after_tax_target_salary, person.after_tax_salary

    print "EBIT", datascope.ebit
    print "REVENUE", datascope.revenue_per_person
    print "MINIMUM HOURLY RATE", datascope.minimum_hourly_rate
