import locale

# set up currency printing
# http://stackoverflow.com/a/320951/564709
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
def currency_str(x):
    return locale.currency(x, grouping=True)
