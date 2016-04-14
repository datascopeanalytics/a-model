import ConfigParser
import datetime


class Person(object):
    def __init__(self, datascope, name, start_date=None,
                 end_date=None, partner_date=None, ownership=0.0):
        # TODO: rename self.datascope -> self.company everywhere
        self.datascope = datascope
        self.name = name
        self.start_date = start_date or datetime.date.today()
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

    def is_active_or_partner(self, date):
        return self.is_active(date) or self.is_partner(date)

    def tax_rate(self, date):
        """calculate the approximate tax rate for this person using the IRS tax
        tables.
        """
        # partners are treated differently due to a variety of factors
        if self.is_partner(date):
            return self.datascope.tax_rate

        # calculate the salary
        factor = (12.0 + self.datascope.n_months_before_tax_bonus) / 12.0
        salary = factor * self.datascope.before_tax_annual_salary

        # use the head of household tables to estimate total tax paid. this
        # isn't perfect, but is a good start
        # http://taxfoundation.org/article/2016-tax-brackets
        tax_table = (
            (13250, 0.100),
            (50400, 0.150),
            (130150, 0.250),
            (210800, 0.280),
            (413350, 0.330),
            (441000, 0.350),
            (float('inf'), 0.396)
        )
        tax = 0.0
        lower_bound = 0.0
        for upper_bound, marginal_rate in tax_table:
            if lower_bound <= salary <= upper_bound:
                tax += marginal_rate * (salary - lower_bound)
                break
            else:
                tax += marginal_rate * (upper_bound - lower_bound)
            lower_bound = upper_bound

        # handle social security taxes
        # https://www.ssa.gov/oact/cola/cbb.html
        social_security_max = 118500
        social_security_rate = 0.062
        tax += social_security_rate * min([salary, social_security_max])

        # handle medicare taxes
        # https://www.irs.gov/taxtopics/tc751.html
        medicare_threshold = 200000
        medicare_rate_low = 0.0145
        medicare_rate_high = medicare_rate_low + 0.009
        tax += medicare_rate_low * min([salary, medicare_threshold])
        if salary > medicare_threshold:
            tax += medicare_rate_high * (salary - medicare_threshold)

        # illinois tax rate
        # http://www.revenue.state.il.us/TaxRates/Income.htm
        il_rate = 0.0375
        tax += il_rate * salary

        return tax / salary

    def fraction_of_year(self, date):
        """returns the fraction of the year (up to `date`) that this person
        worked
        """
        beg_of_year = datetime.date(date.year, 1, 1)
        end_of_year = date
        if self.end_date and self.end_date < beg_of_year:
            return 0.0
        if self.start_date > end_of_year:
            return 0.0
        start_date = max([self.start_date, beg_of_year])
        if self.end_date and self.end_date < end_of_year:
            date = max([self.end_date, beg_of_year])
        # add one to the difference to include beg_of_year
        numerator = (date - start_date).days + 1.0
        denominator = (end_of_year - beg_of_year).days + 1.0
        return numerator / denominator

    def fraction_datascope_year(self, date):
        """returns the fraction of all datascopers' year that this person has
        worked
        """
        total = 0.0
        # iterate over all people here to be sure to capture people leaving
        # mid-year
        for person in self.datascope.iter_people():
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

    def before_tax_target_bonus_dividends(self, date):
        cash_goal = self.datascope.get_annual_cash_goal(date.year)
        profit = cash_goal[-2][1] - cash_goal[-1][1]
        return self.net_fraction_of_profits(date) * profit
