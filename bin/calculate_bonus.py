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
from a_model.company import Company
from a_model.argparsers import CalculateBonusParser

# parse command line arguments
parser = CalculateBonusParser(description=__doc__)
args = parser.parse_args()

# get some credentials from the company object
company = Company(today=args.today)

# get the date for which we are calculating the bonuses
end_of_last_year = datetime.date(args.today.year-1, 12, 31)

# prepare initial spreadsheet as necessary
if args.prepare_csv:
    with open(args.input_csv, 'w') as stream:
        writer = csv.writer(stream)
        writer.writerow(('total bonus pool', 0))
        writer.writerow((
            'name', 'ownership', 'fraction of year', 'award bonus'
        ))
        for person in company.iter_people():
            f = person.fraction_of_year(end_of_last_year)
            if f > 0:
                writer.writerow((
                    person.name,
                    person.ownership,
                    f,
                    0,
                ))
        print args.input_csv, "contains starting point for bonus calculation"
        print "edit that spreadsheet and then re-run this command without -p"
    exit()


class PersonMock(object):
    def __init__(self, row):
        self.name = row['name']
        self.ownership = self.cast_as_float(row['ownership'])
        self.fraction_of_year = self.cast_as_float(row['fraction of year'])
        self.award_bonus = self.cast_as_float(row['award bonus'])

    def cast_as_float(self, s):
        if s == '':
            return 0.0
        return float(s)

# read the bonus pool spreadsheet
people = []
with open(args.input_csv, 'rU') as stream:
    line = stream.readline()
    row = line.split(',', 1)
    if row[0] != 'total bonus pool':
        raise ValueError(
            'expected first row of spreadsheet to specify bonus pool size'
        )
    pool_size = float(row[1])

    reader = csv.DictReader(stream)
    for row in reader:
        person = PersonMock(row)
        people.append(person)

# print out the bonuses for each person
total_time = sum([person.fraction_of_year for person in people])
total_award = sum([person.award_bonus for person in people])
totals = {'dividends': 0.0, 'time_bonus': 0.0, 'award_bonus': 0.0}
print "BONUSES FOR", end_of_last_year.year
print ''
print "{:>12} {:>12} {:>12} {:>12} {:>12}".format(
    'name', 'dividends', 'time bonus', 'award bonus', 'total'
)
f = company.fraction_profit_for_dividends
F = company.fraction_time_bonus
for person in people:
    proportion_time = person.fraction_of_year / total_time
    proportion_award = person.award_bonus / total_award
    dividends = f * pool_size * person.ownership
    time_bonus = (1.0 - f) * F * pool_size * proportion_time
    award_bonus = (1.0 - f) * (1.0 - F) * pool_size * proportion_award
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
