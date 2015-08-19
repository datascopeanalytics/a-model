import locale
import sys
import datetime
import calendar

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
QBO_DATE_FORMAT = '%m/%d/%Y'

def currency_str(x):
    """prettify a float as a currency string"""
    # http://stackoverflow.com/a/320951/564709
    return locale.currency(x, grouping=True)


def print_err(s):
    """print a string to stderr"""
    print >> sys.stderr, s


def qbo_date_str(d):
    """return the date in quickbooks online compatible format"""
    return d.strftime(QBO_DATE_FORMAT)


def qbo_date(s):
    return datetime.datetime.strptime(s, QBO_DATE_FORMAT).date()


def end_of_last_month():
    today = datetime.date.today()
    first_of_month = datetime.date(today.year, today.month, 1)
    return first_of_month - datetime.timedelta(days=1)


def end_of_month(date):
    first_day, last_day = calendar.monthrange(date.year, date.month)
    return datetime.date(date.year, date.month, last_day)


def iter_end_of_months(start_date, end_date):
    date = end_of_month(start_date)
    while date <= end_date:
        yield date
        date += datetime.timedelta(days=1)
        date = end_of_month(date)


def urlencode(params):
    return '&'.join('%s=%s' % (a, b) for a, b in params)
