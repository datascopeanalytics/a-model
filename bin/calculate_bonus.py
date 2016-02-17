#!/usr/bin/env python
"""
This script is used to calculate bonuses for everyone, including dividends for
partners based on a specified bonus pool size.
"""

import datetime

from a_model import reports
from a_model.datascope import Datascope
from a_model.argparsers import CalculateBonusParser

# parse command line arguments
parser = CalculateBonusParser(description=__doc__)
args = parser.parse_args()

print args.exclude

# get some credentials from the datascope object
datascope = Datascope(today=args.today)

# print out the bonuses for each person
end_of_last_year = datetime.date(args.today.year-1, 12, 31)
totals = {'dividends': 0.0, 'time_bonus': 0.0, 'award_bonus': 0.0}
print "BONUSES FOR", end_of_last_year.year
print ''
print "{:>12} {:>12} {:>12} {:>12} {:>12}".format(
    'name', 'dividends', 'time bonus', 'award bonus', 'total'
)
for person in datascope.iter_people():
    if person.name in args.exclude:
        continue
    bonus = person.fraction_bonus(end_of_last_year) * args.pool_size
    if bonus > 0.0:
        dividends = person.fraction_dividends() * args.pool_size
        time_bonus = bonus * datascope.fraction_time_bonus
        award_bonus = 0 #bonus - time_bonus
        person_total = dividends + time_bonus + award_bonus
        totals['dividends'] += dividends
        totals['time_bonus'] += time_bonus
        totals['award_bonus'] += award_bonus
        print "{:>12} {:12,.2f} {:12,.2f} {:12,.2f} {:12,.2f}".format(
            person.name, dividends, time_bonus, award_bonus, person_total,
        )
print ''
print "{:>12} {:12,.2f} {:12,.2f} {:12,.2f} {:12,.2f}".format(
    'TOTAL',
    totals['dividends'],
    totals['time_bonus'],
    totals['award_bonus'],
    sum(totals.values()),
)
