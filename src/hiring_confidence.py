#!/usr/bin/env python
__doc__ = """
The goal of this script is to figure out when its appropriate to change our
staffing so that we can be reasonably confident we're making a good decision.
"""

import argparse

from datascope import Datascope

# parse command line arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    '--n-months',
    metavar='M',
    type=int,
    help='the number of months to simulate',
    default=12,
)
parser.add_argument(
    '--n-universes',
    metavar='U',
    type=int,
    help='the number of universes to simulate',
    default=1000,
)
parser.add_argument(
    '--n-n00bs',
    metavar='N',
    type=int,
    help='the number of new people to add to Datascope',
    default=1,
)
parser.add_argument(
    '-v', '--verbose',
    action="store_true",
    help='print more information during the simulations',
)
args = parser.parse_args()

# simulate datascope revenues before adding a person
datascope = Datascope()
no_n00b_outcomes, no_n00b_cash = datascope.simulate_finances(
    n_months=args.n_months,
    n_universes=args.n_universes,
    verbose=args.verbose,
)

# simulate revenues after adding a person
for n00b in range(args.n_n00bs):
    datascope.add_person("n00b_%d" % n00b)
n00b_outcomes, n00b_cash = datascope.simulate_finances(
    n_months=args.n_months,
    n_universes=args.n_universes,
    verbose=args.verbose,
)

keys = set(n00b_outcomes.keys()).union(set(no_n00b_outcomes.keys()))
for key in keys:
    no_n00b = no_n00b_outcomes[key]
    n00b = n00b_outcomes[key]
    print "%30s%10d%10d%10d" % (key, no_n00b, n00b, n00b - no_n00b)
