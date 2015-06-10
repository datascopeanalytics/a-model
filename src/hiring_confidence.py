"""The goal of this script is to figure out when its appropriate to change our
staffing so that we can be reasonably confident we're making a good decision.

TODO: how to reasonably decide when its a good time to hire, just based on our
cash in the bank. probably something to do with ROI
"""

import sys
import collections
from pprint import pprint

from datascope import Datascope


datascope = Datascope()

# basically what we want to do is simulate starting with a certain amount in
# the bank, and getting paid X in any given month.
n_months = 12
counter = collections.Counter()
simulations = []
n_universes = 1000
for universe in range(n_universes):
    if universe % 100 == 0:
        print "simulation %d" % universe
    is_bankrupt = False
    no_cash = False

    # this game is a gross over simplification. each month datascope pays its
    # expenses and gets paid at the end of the month. This is a terrifying way
    # to run a business---we have quite a bit more information about the
    # business health than "drawing a random number from a black box". For
    # example, we have a sales pipeline, projects underway, and accounts
    # receivable, all of which give us confidence about the current state of
    # affairs beyond the cash on hand at the end of each month.
    cash = initial_cash = datascope.n_months_buffer * datascope.costs()
    for month in range(n_months):
        revenue = datascope.simulate_revenue()
        cash -= datascope.costs()
        if cash < -datascope.line_of_credit:
            is_bankrupt = True
        elif cash < 0:
            no_cash = True
        cash += revenue
    simulations.append(cash)

    # how'd we do this year? if we didn't go bankrupt, are we able to give a
    # bonus? do we have excess profit beyond our target profit so we can grow
    # the business
    profit = cash - initial_cash
    if is_bankrupt:
        counter['bankrupt'] += 1
    elif no_cash:
        counter['survived with line of credit'] += 1
    else:
        counter['not bankrupt'] += 1
        if profit < 0:
            counter['no bonus'] += 1
        if profit > 0:
            counter['is bonus'] += 1
        if profit > n_months * datascope.before_tax_profit():
            counter['can grow business'] += 1

    # TODO: would be nice to look at some plots of these different scenarios

#    print profit

pprint(dict(counter), sys.stderr)
