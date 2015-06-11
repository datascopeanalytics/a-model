#!/usr/bin/env python
__doc__ = """
The goal of this script is to make it easy to quickly explore how everyone's
personal take-home pay goals impact Datascope's goals. To experiment,
manipulate your personal goals by manipulating your desired take home pay to
get a better sense of how your personal goals are tied to Datascope's
profitability (as measured by EBIT and revenue).

Also note how this affects the minimum hourly rate that we need to charge if we
are all working half-time.
"""

import argparse

from datascope import Datascope

# parse command line arguments
parser = argparse.ArgumentParser(description=__doc__)
args = parser.parse_args()

# instantiate datascope
datascope = Datascope()

# calculate the financials from the information provided in config.ini
print "EBIT", datascope.ebit()
print "REVENUE", datascope.revenue_per_person()
print "MINIMUM HOURLY RATE", datascope.minimum_hourly_rate()
print ""
print "PERSONAL TAKE HOME PAY:"
for person in datascope:
    print person.name, person.after_tax_target_salary, person.after_tax_salary()
