import ConfigParser


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
