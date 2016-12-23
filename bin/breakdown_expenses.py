#!/usr/bin/env python
"""
This script is used to breakdown the expenses during a particular fiscal year.
This is helpful for comparing expectations in our budget.
"""

import datetime
import collections

from a_model import reports
from a_model.company import Company
from a_model.argparsers import BreakdownExpensesParser

# parse command line arguments
parser = BreakdownExpensesParser(description=__doc__)
args = parser.parse_args()

# get some credentials from the company object
company = Company(today=args.today)

# get the date for which we are calculating the bonuses
end_of_last_year = datetime.date(args.today.year-1, 12, 31)

historical_personnel_costs = \
    company.profit_loss.get_historical_personnel_costs()
historical_office_costs = company.profit_loss.get_historical_office_costs()


def aggregate_by_year(historical_values):
    aggregate = collections.defaultdict(float)
    for date, value in historical_values:
        aggregate[date.year] += value
    return dict(aggregate)


annual_personnel_costs = aggregate_by_year(historical_personnel_costs)
annual_office_costs = aggregate_by_year(historical_office_costs)

print "{:>6} {:>16} {:>16}".format('year', 'personnel', 'office')
for year in sorted(annual_personnel_costs):
    print "{:>6} {:16,.2f} {:16,.2f}".format(
        year,
        annual_personnel_costs[year],
        annual_office_costs[year],
    )
