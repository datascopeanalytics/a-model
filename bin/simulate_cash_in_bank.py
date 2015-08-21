#!/usr/bin/env python
"""
The goal of this script is to project the cash we will have in the bank over
time.
"""

import sys

from a_model.datascope import Datascope
from a_model.argparsers import SimulationParser

# parse command line arguments
parser = SimulationParser(description=__doc__)
args = parser.parse_args()

# instantiate datascope
datascope = Datascope()

# get past year's worth of cash in bank
historical_cash_in_bank = datascope.balance_sheet.get_historical_cash_in_bank()
print historical_cash_in_bank

# simulate cashflow for the rest of the year
monthly_cash_outcomes = datascope.simulate_monthly_cash(
    n_months=args.n_months,
    n_universes=args.n_universes,
    verbose=args.verbose,
)
print monthly_cash_outcomes
