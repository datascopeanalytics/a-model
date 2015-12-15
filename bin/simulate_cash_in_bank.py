#!/usr/bin/env python
"""
The goal of this script is to project the cash we will have in the bank over
time.
"""

import sys
import datetime
import math
import collections

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy
import matplotlib
import matplotlib.patheffects as patheffects

from a_model.datascope import Datascope
from a_model.argparsers import SimulationParser

# parse command line arguments
parser = SimulationParser(description=__doc__)
args = parser.parse_args()

# instantiate datascope
datascope = Datascope()

# get past year's worth of cash in bank
historical_cash_in_bank = datascope.balance_sheet.get_historical_cash_in_bank()

# simulate cashflow for the rest of the year
monthly_cash_outcomes = datascope.simulate_monthly_cash(
    n_months=args.n_months,
    n_universes=args.n_universes,
    verbose=args.verbose,
)

# transform the data in a convenient way for plotting
historical_t, historical_cash = zip(*historical_cash_in_bank)
max_cash = max(historical_cash)
monthly_t = [historical_t[-1]]
monthly_t += [t for t in datascope.iter_future_months(args.n_months)]
for monthly_cash in monthly_cash_outcomes:
    monthly_cash.insert(0, historical_cash[-1])
median_monthly_cash = []
for month_of_cash in zip(*monthly_cash_outcomes):
    median_monthly_cash.append(numpy.median(month_of_cash))
    max_cash = max(max_cash, max(month_of_cash))

# set the domain of the graph
t_domain = [
    datascope.balance_sheet.start_date,
    max(monthly_t)+datetime.timedelta(days=1),
]
yunit = datascope.line_of_credit
ymax = math.ceil(max_cash / yunit) * yunit
plt.axis(t_domain + [-yunit, ymax])
ax = plt.gca()
ax.set_autoscale_on(False)

matplotlib.rc('font', size=10)

# format the xaxis
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.gcf().autofmt_xdate()

# format the yaxis
yticks = numpy.arange(-yunit, ymax+1, yunit)
yticklabels = ["%dk" % (y/1000) for y in yticks]
plt.yticks(yticks, yticklabels)

# plot the historical data
historical_params = {
    'color': '#e41a1c',
    'linewidth': 2,
}
plt.plot(historical_t, historical_cash, **historical_params)

# plot the simulations
for monthly_cash in monthly_cash_outcomes:
    plt.plot(monthly_t, monthly_cash, color='#999999', alpha=0.04)

# plot the median
plt.plot(monthly_t, median_monthly_cash, linestyle='--', **historical_params)

# plot the zero line where we need to dip into line of credit
plt.plot(t_domain, [0] * len(t_domain), color='k')

# cash buffer line
goal_styles = {
    'color': 'k',
    'linestyle': '--',
}
cash_buffer = datascope.get_cash_buffer()
plt.plot(t_domain, [cash_buffer] * len(t_domain), **goal_styles)

# plot the goal lines
years = range(t_domain[0].year, t_domain[1].year+1)
for year in years:
    current_year = [datetime.date(year, 1, 1), datetime.date(year, 12, 31)]
    cash_goal = [
        cash_buffer,
        cash_buffer + 12 * datascope.after_tax_target_profit(current_year[-1]),
    ]
    plt.plot(current_year, cash_goal, **goal_styles)

# axis labels
plt.ylabel('cash in bank')

# compute the outcomes of all the simulations at the end of this year
eoy = datetime.date(datetime.date.today().year, 12, 31)
months_until_eoy = datascope.profit_loss.get_months_from_now(eoy)
outcomes = datascope.get_outcomes_in_month(
    months_until_eoy, monthly_cash_outcomes
)

# outcome labels
# http://matplotlib.org/examples/pylab_examples/multiline.html
# http://matplotlib.org/examples/pylab_examples/patheffect_demo.html
label_style = {
    'horizontalalignment': 'right',
    'path_effects': [patheffects.withStroke(linewidth=2, foreground="w")],
}
outcome_format = '{:.0%}'
plt.text(
    eoy, cash_goal[-1],
    'goal\n' + outcome_format.format(outcomes['goal']),
    verticalalignment='bottom',
    **label_style
)
plt.text(
    eoy, cash_buffer,
    'buffer\n' + outcome_format.format(outcomes['buffer']),
    verticalalignment='bottom',
    **label_style
)
plt.text(
    eoy, cash_buffer/2,
    'no bonus\n' + outcome_format.format(outcomes['no bonus']),
    verticalalignment='center',
    **label_style
)
plt.text(
    eoy, -datascope.line_of_credit / 20.0,
    'squeak by\n' + outcome_format.format(outcomes['squeak by']),
    verticalalignment='top',
    **label_style
)
plt.text(
    eoy, -datascope.line_of_credit,
    'bye bye\n' + outcome_format.format(outcomes['bye bye']),
    **label_style
)

# get rid of the axis frame
# http://stackoverflow.com/a/28720127/564709
ax.spines['top'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['right'].set_visible(False)

# get rid of the tick marks while keeping the tick labels
# http://stackoverflow.com/a/20416681/564709
for tic in ax.xaxis.get_major_ticks():
    tic.tick1On = tic.tick2On = False
for tic in ax.yaxis.get_major_ticks():
    tic.tick2On = False

# other labels
filename = 'cash_in_bank.png'
plt.savefig(filename)
print "results now available in", filename
