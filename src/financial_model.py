"""The goal of this script is to make it easy to quickly explore how everyone's
personal take-home pay goals impact Datascope's goals
"""

import os

from datascope import Datascope


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datascope = Datascope(os.path.join(project_root, 'config.ini'))


print "EBIT", datascope.ebit
print "REVENUE", datascope.revenue_per_person
print "MINIMUM HOURLY RATE", datascope.minimum_hourly_rate
print ""
print "PERSONAL TAKE HOME PAY:"
for person in datascope:
    print person.name, person.after_tax_target_salary, person.after_tax_salary
