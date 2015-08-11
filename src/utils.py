import locale
import sys
import datetime
import calendar

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


def currency_str(x):
    """prettify a float as a currency string"""
    # http://stackoverflow.com/a/320951/564709
    return locale.currency(x, grouping=True)


def print_err(s):
    """print a string to stderr"""
    print >> sys.stderr, s


def qbo_date_str(d):
    """return the date in quickbooks online compatible format"""
    return d.strftime('%Y/%m/%d')


def end_of_last_month():
    today = datetime.date.today()
    first_of_month = datetime.date(today.year, today.month, 1)
    return first_of_month - datetime.timedelta(days=1)
