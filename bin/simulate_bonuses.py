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

from a_model.datascope import Datascope
from a_model.argparsers import SimulationParser
from a_model import utils

# parse command line arguments
parser = SimulationParser(description=__doc__)
args = parser.parse_args()

# instantiate datascope
datascope = Datascope()

# simulate cashflow for the rest of the year
monthly_cash_outcomes = datascope.get_or_simulate_monthly_cash(
    n_months=args.n_months,
    n_universes=args.n_universes,
    verbose=args.verbose,
)

# slice the data to get the eoy cash
eoy = datetime.date(datetime.date.today().year, 12, 31)
months_until_eoy = datascope.profit_loss.get_months_from_now(eoy)
cash_buffer = datascope.n_months_buffer * datascope.costs()
person_bonuses = []
for monthly_cash in monthly_cash_outcomes:
    eoy_cash = monthly_cash[months_until_eoy]
    profit = eoy_cash - cash_buffer
    for person in datascope:
        bonus = max(0, profit * person.net_fraction_of_profits())
        person_bonuses.append((person.name, bonus))

# cast the data as a dataframe
df = pd.DataFrame(person_bonuses, columns=['name', 'bonus'])

# configure seaborn
palette = sns.color_palette(palette='Set1')

# quick with all the dots sampled over the top
# http://stanford.io/1LLujlf
ax = sns.boxplot(x='name', y='bonus', data=df, color=palette[0], fliersize=0)
sns.stripplot(x='name', y='bonus', data=df,
              jitter=True, size=3, color=".3", linewidth=0, alpha=0.1)

# add the goal lines for each person
for i, person in enumerate(datascope):
    goal = 12 * person.before_tax_target_bonus_dividends()
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
