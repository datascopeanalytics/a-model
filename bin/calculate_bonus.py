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

# get some credentials from the datascope object
datascope = Datascope(today=args.today)

# print out the bonuses for each person
end_of_last_year = datetime.date(args.today.year-1, 12, 31)
print "BONUSES FOR", end_of_last_year.year
print ''
print "%20s  %10s  %10s  %10s  %10s" % (
    'name', 'dividends', 'time bonus', 'award bonus', 'total'
)
for person in datascope.iter_people():
    dividends = person.fraction_dividends() * args.pool_size
    bonus = person.fraction_bonus(end_of_last_year) * args.pool_size
    if bonus > 0.0:
        time_bonus = bonus * datascope.fraction_time_bonus
        award_bonus = 0 #bonus - time_bonus
        total = dividends + time_bonus + award_bonus
        print "{:>20} ${:10,.2f} ${:10,.2f} ${:10,.2f} ${:10,.2f}".format(
            person.name, dividends, time_bonus, award_bonus, total,
        )
