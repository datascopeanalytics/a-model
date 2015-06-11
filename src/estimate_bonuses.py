#!/usr/bin/env python
__doc__ = """

The goal of this script is to, based on YTD cash and simulated cash flows,
estimate the size of the bonus pool and each person's resulting salary.

"""

import argparse
import datetime
from pprint import pprint
import sys
import numpy

from datascope import Datascope

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
print -datascope.line_of_credit, 0.0
print -datascope.line_of_credit, 1.0
print ''
# current cash situation
print datascope.current_cash_in_bank, 0.0
print datascope.current_cash_in_bank, 1.0
print ''
# six month buffer
cash_buffer = datascope.n_months_buffer * datascope.costs()
print cash_buffer, 0.0
print cash_buffer, 1.0
print ''
# target bonus level
print cash_buffer + 12*datascope.before_tax_profit(), 0.0
print cash_buffer + 12*datascope.before_tax_profit(), 1.0
print ''

# given that there will be a bonus, calculate the median bonus for each person
print >> sys.stderr, "P(NO BONUS) =", float(eoy_outcomes['no bonus']) / args.n_universes
print >> sys.stderr, "P(BONUS) =", float(eoy_outcomes['is bonus']) / args.n_universes
for person in datascope.people:
    person.bonus_outcomes = []
for eoy_cash in eoy_cash_list:
    profit = eoy_cash - cash_buffer
    if profit > 0:
        for person in datascope.people:
            person.bonus_outcomes.append(profit * person.net_fraction_of_profits())
print >> sys.stderr, "%10s %8s %8s %8s" % (
    "name","25pct", "50pct", "75pct"
)
for person in datascope.people:
    print >> sys.stderr, "%10s %8.0f %8.0f %8.0f" % (
        person.name,
        numpy.percentile(person.bonus_outcomes, 25),
        numpy.percentile(person.bonus_outcomes, 50),
        numpy.percentile(person.bonus_outcomes, 75),
    )
