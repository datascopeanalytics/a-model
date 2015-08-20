#!/usr/bin/env python
"""
The goal of this script is to figure out when its appropriate to change our
staffing so that we can be reasonably confident we're making a good decision.
"""

from a_model.datascope import Datascope
from a_model.argparsers import HiringParser

# parse command line arguments
parser = HiringParser(description=__doc__)
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
print "This script ran simulations over the next %d months" % args.n_months
print "and here are the results..."
print ""
print "%30s%10s%10s%10s" % (
    '',
    'current',
    '%d n00bs' % args.n_n00bs,
    'change',
)
print '-' * 79
for key in keys:
    no_n00b = float(no_n00b_outcomes[key])
    n00b = float(n00b_outcomes[key])
    print "%30s%10.3f%10.3f%10.3f" % (
        key,
        no_n00b / args.n_universes,
        n00b / args.n_universes,
        (n00b - no_n00b) / args.n_universes,
    )
print '-' * 79
