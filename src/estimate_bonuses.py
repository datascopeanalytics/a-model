#!/usr/bin/env python
"""
The goal of this script is to, based on YTD cash and simulated cash flows,
estimate the size of the bonus pool and each person's resulting salary.
"""

import argparse
import datetime
from pprint import pprint
import sys
import numpy

from datascope import Datascope
from utils import currency_str, print_err


# parse command line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    '--n-universes',
    metavar='U',
    type=int,
    help='the number of universes to simulate',
    default=1000,
)
parser.add_argument(
    '-v', '--verbose',
    action="store_true",
    help='print more information during the simulations',
)
args = parser.parse_args()

# instantiate datascope
datascope = Datascope()

# simulate cashflow for the rest of the year
today = datetime.date.today()
n_months = 12 - today.month + 1
eoy_outcomes, eoy_cash_list = datascope.simulate_finances(
    n_months=n_months,
    n_universes=args.n_universes,
    initial_cash=datascope.current_cash_in_bank,
    verbose=args.verbose,
)

# print out data to be plotted in xmgrace
# ./estimate_bonuses.py | xmagrace -
eoy_cash_list.sort()
for i, eoy_cash in enumerate(eoy_cash_list):
    print eoy_cash, 1.0-float(i)/args.n_universes
print ''
# go bankrupt
print -datascope.line_of_credit, 0.0, '""'
print -datascope.line_of_credit, 1.0, '"busted"'
print ''
# current cash situation
print datascope.current_cash_in_bank, 0.0, '""'
print datascope.current_cash_in_bank, 1.0, '"bank"'
print ''
# six month buffer
cash_buffer = datascope.n_months_buffer * datascope.costs()
print cash_buffer, 0.0, '""'
print cash_buffer, 1.0, r'"%i-month\nbuffer"' % datascope.n_months_buffer
print ''
# target bonus level
print cash_buffer + 12*datascope.before_tax_profit(), 0.0, '""'
print cash_buffer + 12*datascope.before_tax_profit(), 1.0, '"target"'
print ''
# expected bonus
index = len(eoy_cash_list) / 2 # hack
print eoy_cash_list[index], 0.0, '""'
print eoy_cash_list[index], 1.0, '"expected"'
print ''

# given that there will be a bonus, calculate the median bonus for each person
print_err("This script just ran simulations for %d months" % n_months)
print_err("and here are the different outcomes that we can expect...")
print_err("")
print_err("P(NO BONUS) = %.2f" % (float(eoy_outcomes['no bonus']) / args.n_universes))
print_err("P(BONUS) = %.2f" % (float(eoy_outcomes['is bonus']) / args.n_universes))
for person in datascope.people:
    person.bonus_outcomes = []
for eoy_cash in eoy_cash_list:
    profit = eoy_cash - cash_buffer
    if profit > 0:
        for person in datascope.people:
            person.bonus_outcomes.append(
                profit * person.net_fraction_of_profits()
            )
print_err("")
print_err("BONUS OUTCOMES EXPECTED AT THE END OF THIS YEAR")
print_err("%10s %15s %15s %15s %15s %15s" % (
    "", "5pct", "25pct", "50pct", "75pct", "95pct",
))
for person in datascope.people:
    print_err("%10s %15s %15s %15s %15s %15s" % (
        person.name,
        currency_str(numpy.percentile(person.bonus_outcomes, 5)),
        currency_str(numpy.percentile(person.bonus_outcomes, 25)),
        currency_str(numpy.percentile(person.bonus_outcomes, 50)),
        currency_str(numpy.percentile(person.bonus_outcomes, 75)),
        currency_str(numpy.percentile(person.bonus_outcomes, 95)),
    ))
