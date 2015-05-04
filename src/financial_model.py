import os

from datascope import Datascope


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datascope = Datascope(os.path.join(project_root, 'config.ini'))


print "EBIT", datascope.ebit
print "REVENUE", datascope.revenue_per_person
print "MINIMUM HOURLY RATE", datascope.minimum_hourly_rate

for person in datascope:
    print person.name, person.after_tax_target_salary, person.after_tax_salary
