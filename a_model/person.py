import ConfigParser
import datetime


class Person(object):
    def __init__(self, datascope, name, start_date,
                 end_date=None, partner_date=None, ownership=0.0):
        self.datascope = datascope
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.partner_date = partner_date
        self.ownership = ownership

    def __repr__(self):
        return '<Person: %s>' % self.name.title()

    def is_active(self, date):
        if date < self.start_date:
            return False
        elif self.end_date and date > self.end_date:
            return False
        return True

    def is_partner(self, date):
        return self.partner_date and date >= self.partner_date

    @property
    def after_tax_target_salary(self):
        """This is on a per month basis, but includes biweekly salary as well
        as annual bonus and dividends. If the target take home pay is not
        specified, then we estimate the target take home pay from the monthly
        after tax pay and the number of months of after tax bonus expected at
        the end of the year.
        """
        default_pay = self.datascope.after_tax_salary
        default_pay *= (1 + self.datascope.n_months_after_tax_bonus/12)
        try:
            pay = self.datascope.config.getfloat('take home pay', self.name)
        except (ConfigParser.NoOptionError, ValueError):
            pay = default_pay
        return pay

    def fraction_of_year(self, date):
        """returns the fraction of the year (up to `date`) that this person
        worked
        """
        beg_of_year = datetime.date(date.year, 1, 1)
        end_of_year = date
        if self.end_date and self.end_date < end_of_year:
            date = max([self.end_date or date, beg_of_year])
        numerator = (date - beg_of_year).days
        denominator = (end_of_year - beg_of_year).days
        return float(numerator) / denominator

    def fraction_datascope_year(self, date):
        """returns the fraction of all datascopers' year that this person has
        worked
        """
        total = 0.0
        for person in self.datascope:
            total += person.fraction_of_year(date)
        return self.fraction_of_year(date) / total

    def fraction_dividends(self):
        """Fraction of profits that come in the form of a dividend"""
        return self.datascope.fraction_profit_for_dividends * self.ownership

    def fraction_bonus(self, date):
        """Fraction of profits that come in the form of a bonus"""
        return (1.0-self.datascope.fraction_profit_for_dividends) * \
            self.fraction_datascope_year(date)

    def net_fraction_of_profits(self, date):
        """Net fraction of all profits"""
        return self.fraction_dividends() + self.fraction_bonus(date)

    def after_tax_target_salary_from_bonus_dividends(self):
        return self.after_tax_target_salary - self.datascope.after_tax_salary

    def after_tax_salary_from_bonus(self):
        return self.fraction_bonus() *\
            self.datascope.after_tax_target_profit()

    def after_tax_salary_from_dividends(self):
        return self.fraction_dividends() *\
            self.datascope.after_tax_target_profit()

    def after_tax_salary(self):
        return (
            self.after_tax_salary_from_bonus() +
            self.after_tax_salary_from_dividends() +
            self.datascope.after_tax_salary
        )

    def before_tax_target_bonus_dividends(self):
        # only bonuses are taxed at tax rate.
        target_bonus = \
            self.after_tax_salary_from_bonus() / (1 - self.datascope.tax_rate)
        target_dividends = self.after_tax_salary_from_dividends()
        return target_bonus + target_dividends
