import os
import ConfigParser

import numpy

def median(a):
    b = [_ for _ in a]
    b.sort()
    mid = len(b)/2
    if len(b) % 2 == 1:
        return b[mid]
    else:
        return (b[mid] + b[mid+1])/2.0


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
            pay *= (1 + self.datascope.config.getfloat('parameters', 'n_months_after_tax_bonus')/12)
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

    @property
    def n_people(self):
        return len(self.people)

    @property
    def n_partners(self):
        return len([person for person in self if person.is_partner])

    @property
    def fraction_profit_for_dividends(self):
        return self.config.getfloat('parameters', 'fraction_profit_for_dividends')

    @property
    def after_tax_salary(self):
        return self.config.getfloat('parameters', 'monthly_after_tax_pay')

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


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datascope = Datascope(os.path.join(project_root, 'config.ini'))
    print datascope.n_people, datascope.n_partners
    for person in datascope:
        print person.name, person.after_tax_target_salary, person.ownership, person.net_fraction_of_profits

    print "DATASCOPE AFTER TAX TARGET PROFIT"
    print datascope.after_tax_target_profit

    for person in datascope:
        print person.name, person.after_tax_target_salary, person.after_tax_salary
