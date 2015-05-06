"""The goal of this script is to figure out when its appropriate to change our
staffing so that we can be reasonably confident we're making a good decision
"""

import os
import sys

from datascope import Datascope


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datascope = Datascope(os.path.join(project_root, 'config.ini'))

# basically what we want to do is simulate starting with a certain amount in
# the bank, and getting paid X in any given month.
n_failures = 0
for universe in range(1000):
    cash = cash0 = datascope.n_months_buffer * datascope.costs
    for month in range(12):
        revenue = datascope.simulate_revenue()
        cash -= datascope.costs
        # print month, revenue, cash
        if cash < 0:
            n_failures += 1
            break
        cash += revenue
    print cash - cash0

print >> sys.stderr, "#datascopefail counter:", n_failures
