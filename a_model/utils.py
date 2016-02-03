import locale
import sys
import datetime
import calendar
import os

from dateutil import relativedelta

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
QBO_DATE_FORMAT = '%m/%d/%Y'

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DROPBOX_ROOT = os.path.join(PROJECT_ROOT, 'Dropbox')
DATA_ROOT = os.path.join(PROJECT_ROOT, '.data')

MAX_CACHE_AGE = 60 * 60 * 24 * 14


def currency_str(x, *args, **kwargs):
    """prettify a float as a currency string"""
    # http://stackoverflow.com/a/320951/564709
    return locale.currency(x, grouping=True)


def thousands_currency_str(x, *args, **kwargs):
    s = currency_str(x/1000., *args, **kwargs)
    return s.rsplit('.', 1)[0] + 'k'


def urlencode(params):
    return '&'.join('%s=%s' % (a, b) for a, b in params)


# methods for parsing the date
def qbo_date_str(d):
    """return the date in quickbooks online compatible format"""
    return d.strftime(QBO_DATE_FORMAT)


def qbo_date(s):
    return datetime.datetime.strptime(s, QBO_DATE_FORMAT).date()


def end_of_last_month(today=None):
    today = today or datetime.date.today()
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


def date_in_n_months(n_months):
    date = end_of_last_month()
    date += relativedelta.relativedelta(months=n_months)
    return end_of_month(date)
