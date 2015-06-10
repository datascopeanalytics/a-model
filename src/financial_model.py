"""The goal of this script is to make it easy to quickly explore how everyone's
personal take-home pay goals impact Datascope's goals
"""

from datascope import Datascope


datascope = Datascope()


print "EBIT", datascope.ebit()
print "REVENUE", datascope.revenue_per_person()
print "MINIMUM HOURLY RATE", datascope.minimum_hourly_rate()
print ""
print "PERSONAL TAKE HOME PAY:"
for person in datascope:
    print person.name, person.after_tax_target_salary, person.after_tax_salary()
