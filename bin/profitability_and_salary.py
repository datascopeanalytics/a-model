#!/usr/bin/env python
"""
The goal of this script is to make it easy to quickly explore how everyone's
personal take-home pay goals impact Datascope's goals. To experiment,
manipulate your personal goals by manipulating your desired take home pay to
get a better sense of how your personal goals are tied to Datascope's
profitability (as measured by EBIT and revenue).

Also note how this affects the minimum hourly rate that we need to charge if we
are all working half-time.
"""

import argparse

from a_model.datascope import Datascope
from a_model.utils import currency_str

# parse command line arguments
parser = argparse.ArgumentParser(description=__doc__)
args = parser.parse_args()

# instantiate datascope
datascope = Datascope()

# calculate the financials from the information provided in config.ini
print "If we met the happiness goals we have, we would have the "
print "following outcomes..."
print ""
print "%40s%16s" % ("EBIT", '{:.2%}'.format(datascope.ebit()))
print "%40s%15s" % (
    "REVENUE PER PERSON",
    currency_str(datascope.revenue_per_person()),
)
print "%40s%15s" % (
    "MINIMUM HOURLY RATE",
    currency_str(datascope.minimum_hourly_rate()),
)
print ""
print "PERSONAL MONTHLY TAKE HOME PAY:"
for person in datascope:
    print "%10s%15s%15s" % (
        person.name,
        currency_str(person.after_tax_target_salary),
        currency_str(person.after_tax_salary()),
    )
