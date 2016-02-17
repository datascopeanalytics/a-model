#!/usr/bin/env python
"""
This script is used to calculate bonuses for everyone, including dividends for
partners based on a specified bonus pool size. To begin, run this script with
the -p/--prepare-csv flag. This will print out a spreadsheet that includes all
of the people that are in our roster and eligible for a bonus as of the end of
the year. It will populate it with currently available ownership numbers and
the fraction of the year that each person was at Datascope for the previous
year.
"""

import datetime
import csv

from a_model import reports
from a_model.datascope import Datascope
from a_model.argparsers import CalculateBonusParser

# parse command line arguments
parser = CalculateBonusParser(description=__doc__)
args = parser.parse_args()

# get some credentials from the datascope object
datascope = Datascope(today=args.today)

# get the date for which we are calculating the bonuses
end_of_last_year = datetime.date(args.today.year-1, 12, 31)

# prepare initial spreadsheet
if args.prepare_csv:
    with open('bonus.csv', 'w') as stream:
        writer = csv.writer(stream)
        writer.writerow((
            'name', 'ownership', 'fraction of year', 'award bonus'
        ))
        for person in datascope.iter_people():
            f = person.fraction_of_year(end_of_last_year)
            if f > 0:
                writer.writerow((
                    person.name,
                    person.ownership,
                    f,
                    'tktk',
                ))
        print stream.name, "contains starting point for bonus calculation"
    exit()

# print out the bonuses for each person
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
