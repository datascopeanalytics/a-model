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
        writer.writerow(('profit sharing pool', 0))
        writer.writerow(('golden six pack amount', 0))
        writer.writerow((
            'name', 'ownership', 'fraction of year', 'n golden six packs',
            'golden six pack awards'
        ))
        # TODO: this does not print out former partners that have left
        for person in company.iter_people_and_partners(end_of_last_year):
            f = person.fraction_of_year(end_of_last_year)
            if f > 0:
                writer.writerow((
                    person.name,
                    person.ownership,
                    f,
                    0,
                    '',
                ))
        print args.input_csv, "contains starting point for bonus calculation"
        print "edit that spreadsheet and then re-run this command without -p"
    exit()


class PersonMock(object):
    def __init__(self, row):
        self.name = row['name']
        self.ownership = self.cast_as_float(row['ownership'])
        self.fraction_of_year = self.cast_as_float(row['fraction of year'])
        self.n_golden_six_packs = self.cast_as_float(row['n golden six packs'])
        self.golden_six_packs = row['golden six pack awards'].split(',')

    def cast_as_float(self, s):
        if s == '':
            return 0.0
        return float(s)

# read the bonus pool spreadsheet
people = []
with open(args.input_csv, 'rU') as stream:

    # get the bonus pool amount
    line = stream.readline()
    row = line.split(',')
    if row[0] != 'profit sharing pool':
        raise ValueError(
            'expected first row of spreadsheet to specify '
            '"profit sharing pool"'
        )
    pool_size = float(row[1])

    # get the golden six pack value
    line = stream.readline()
    row = line.split(',')
    if row[0] != 'golden six pack value':
        raise ValueError((
            'expected second row of spreadsheet to specify '
            '"golden six pack value"'
        ))
    golden_six_pack_value = float(row[1])

    reader = csv.DictReader(stream)
    for row in reader:
        person = PersonMock(row)
        people.append(person)

def write_row(writer, *row):
    if len(row) == 1:
        print ''.join(row)
    else:
        if isinstance(row[1], (float, long, int)):
            fmt = "{:>20} {:12,.2f} {:12,.2f} {:12,.2f} {:12,.2f}"
        else:
            fmt = "{:>20} {:>12} {:>12} {:>12} {:>12}"
        print fmt.format(*row)
    writer.writerow(row)

# print out the bonuses for each person
total_time = sum([person.fraction_of_year for person in people])
total_golden_six_packs = sum([person.n_golden_six_packs for person in people])
total_golden_six_pack_value = total_golden_six_packs * golden_six_pack_value
f = company.fraction_profit_for_dividends
total_time_bonus = pool_size * (1 - f) - total_golden_six_pack_value
totals = {'dividends': 0.0, 'time_bonus': 0.0, 'award_bonus': 0.0}
print "BONUSES FOR", end_of_last_year.year
print ''
with open(args.output_csv, 'w') as stream:
    writer = csv.writer(stream)
    write_row(
        writer, 'name', 'dividends', 'time bonus', 'award bonus', 'total'
    )

    for person in people:
        proportion_time = person.fraction_of_year / total_time
        time_bonus = proportion_time * total_time_bonus
        award_bonus = person.n_golden_six_packs * golden_six_pack_value
        dividends = f * pool_size * person.ownership
        person_total = dividends + time_bonus + award_bonus
        totals['dividends'] += dividends
        totals['time_bonus'] += time_bonus
        totals['award_bonus'] += award_bonus
        write_row(
            writer,
            person.name, dividends, time_bonus, award_bonus, person_total,
        )

    write_row(writer, '')
    write_row(
        writer, 'TOTAL', totals['dividends'], totals['time_bonus'],
        totals['award_bonus'], sum(totals.values()),
    )
