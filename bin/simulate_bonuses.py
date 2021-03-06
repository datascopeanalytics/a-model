#!/usr/bin/env python
"""
Simulate cashflow and estimate how much will be available for each person's
bonus at the end of the year.
"""
import datetime

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import pandas as pd

from a_model.company import Company
from a_model.argparsers import SimulationParser
from a_model import utils

# parse command line arguments
parser = SimulationParser(description=__doc__)
args = parser.parse_args()

# instantiate company
company = Company(today=args.today)

# simulate cashflow for the rest of the year
_, bonus_pool_outcomes, _ = company.simulate_monthly_cash(
    **args.simulate_monthly_cash_kwargs()
)

# slice the data to get the eoy cash
eoy = datetime.date(datetime.date.today().year, 12, 31)
person_bonuses = []
for bonus_pool in bonus_pool_outcomes:
    for person in company.iter_people_and_partners(date=eoy):
        bonus = bonus_pool * person.net_fraction_of_profits(eoy)
        person_bonuses.append((person.name.split()[0].capitalize(), bonus))

# cast the data as a dataframe
x, y = '', 'dividend + pre-tax bonus'
df = pd.DataFrame(person_bonuses, columns=[x, y])

# configure seaborn
palette = sns.color_palette(palette='Set1')

# quick with all the dots sampled over the top
# http://stanford.io/1LLujlf
ax = sns.boxplot(x=x, y=y, data=df, color=palette[0], fliersize=0)
sns.stripplot(x=x, y=y, data=df,
              jitter=True, size=3, color=".3", linewidth=0, alpha=0.1)

# add the goal lines for each person
for i, person in enumerate(company.iter_people_and_partners(date=eoy)):
    goal = person.before_tax_target_bonus_dividends(eoy)
    ax.plot([i-0.5, i+0.5], [goal, goal], color='k', linestyle='--')

# set the y-axis domain
ymin, ymax = ax.get_ylim()
ax.set_ylim(0, ymax)

# set the y-axis to be formatted nicely
# http://matplotlib.org/examples/pylab_examples/custom_ticker1.html
currency = FuncFormatter(utils.thousands_currency_str)
ax.yaxis.set_major_formatter(currency)

# save to disk
filename = 'bonuses.png'
plt.savefig(filename)
print "results now available in", filename
