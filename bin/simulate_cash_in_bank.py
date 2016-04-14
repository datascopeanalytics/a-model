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

from a_model.company import Company
from a_model.argparsers import SimulationParser
from a_model.utils import iter_end_of_months, currency_str

# parse command line arguments
parser = SimulationParser(description=__doc__)
args = parser.parse_args()

# instantiate company
company = Company(today=args.today)

# get past year's worth of cash in bank
historical_cash_in_bank = company.balance_sheet.get_historical_cash_in_bank()

# simulate cashflow for the rest of the year
outcomes = company.simulate_monthly_cash(
    n_months=args.n_months,
    n_universes=args.n_universes,
    verbose=args.verbose,
    ontime_payment=args.ontime_payment,
    ontime_completion=args.ontime_completion,
)
monthly_cash_outcomes = outcomes[0]
bonus_pool_outcomes = outcomes[1]
quarterly_tax_outcomes = outcomes[2]

# compute the outcomes of all the simulations at the end of this year. don't
# plot the 'bye bye' one because it never happens and, even if it did, its
# likelihood can always be inferred by adding the rest of them
eoy = datetime.date(args.today.year, 12, 31)
months_until_eoy = company.profit_loss.get_months_from_now(eoy)
outcomes = company.get_outcomes_in_month(
    months_until_eoy, monthly_cash_outcomes,
)
outcomes.popitem()

# transform the data in a convenient way for plotting
historical_t, historical_cash = zip(*historical_cash_in_bank)
max_cash = max(historical_cash)
monthly_t = [historical_t[-1]]
monthly_t += [t for t in company.iter_future_months(args.n_months)]
for monthly_cash in monthly_cash_outcomes:
    monthly_cash.insert(0, historical_cash[-1])
median_monthly_cash = []
for month_of_cash in zip(*monthly_cash_outcomes):
    median_monthly_cash.append(numpy.median(month_of_cash))
    max_cash = max(max_cash, max(month_of_cash))

# set the domain of the graph
t_domain = [
    company.balance_sheet.start_date,
    max(monthly_t)+datetime.timedelta(days=1),
]
yunit = company.line_of_credit
ymax = (math.ceil(max_cash / yunit) + 1) * yunit
plt.axis(t_domain + [-yunit, ymax])
ax = plt.gca()
ax.set_autoscale_on(False)

matplotlib.rc('font', size=10)

outcome_scheme = plt.cm.RdGy
outcome_colors = [
    outcome_scheme(0.9),
    outcome_scheme(0.8),
    outcome_scheme(0.2),
    outcome_scheme(0.1),
]

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
    'color': outcome_scheme(1.0),
    'linewidth': 2,
}
plt.plot(historical_t, historical_cash, **historical_params)

# plot the simulations
alpha = 0.3 / math.log(args.n_universes)
for monthly_cash in monthly_cash_outcomes:
    plt.plot(monthly_t, monthly_cash, color='w', alpha=alpha)

# plot the median
plt.plot(monthly_t, median_monthly_cash, linestyle='--', **historical_params)

# plot the zero line where we need to dip into line of credit
outcome_region_params = {
    'alpha': 0.8,
    'edgecolor': 'w',
    'linewidths': 0,
}
plt.fill_between(
    t_domain, 0, -company.line_of_credit,
    facecolor=outcome_colors[3],
    **outcome_region_params
)

# plot the buffer, buffer+bonus and goal bonus zones
goal_dates, cash_buffers, cash_goals = [], [], []
eoy_cash_buffer, eoy_cash_goal = None, None
for date in iter_end_of_months(t_domain[0], t_domain[1]):
    cash_buffer = company.get_cash_buffer(date)
    if date.month == 1:
        goal_dates.append(datetime.date(date.year, date.month, 1))
        cash_buffers.append(cash_buffer)
        cash_goals.append(cash_buffer)
    goal_dates.append(date)
    cash_buffers.append(cash_buffer)
    cash_goals.append(company.get_cash_goal(date))
    if date == eoy:
        eoy_cash_buffer = cash_buffers[-1]
        eoy_cash_goal = cash_goals[-1]
plt.fill_between(
    goal_dates, 0, cash_buffers,
    facecolor=outcome_colors[2],
    **outcome_region_params
)
plt.fill_between(
    goal_dates, cash_goals, cash_buffers,
    facecolor=outcome_colors[1],
    **outcome_region_params
)
plt.fill_between(
    goal_dates, cash_goals, ymax,
    facecolor=outcome_colors[0],
    **outcome_region_params
)

# axis labels
plt.ylabel('cash in bank')

# outcome labels
# http://matplotlib.org/examples/pylab_examples/multiline.html
# http://matplotlib.org/examples/pylab_examples/patheffect_demo.html
ys = [
    (ymax + eoy_cash_goal) / 2,
    (eoy_cash_goal + cash_buffer) / 2,
    cash_buffer/2,
    -company.line_of_credit / 2,
]
for key, y, color in zip(outcomes, ys, outcome_colors):
    plt.text(
        eoy - datetime.timedelta(days=30),
        y,
        key + '\n' + '{:.0%}'.format(outcomes[key]),
        horizontalalignment='right',
        color=color,
        path_effects=[patheffects.withStroke(linewidth=2, foreground="w")],
        verticalalignment='center',
    )

# add a vertical goal line to make it easier to see the results
plt.plot([eoy, eoy], [-yunit, ymax], linestyle='--', color='w', linewidth=2)

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

# save results to file and print a few other useful summary statistics
filename = 'cash_in_bank.png'
plt.savefig(filename)
print "results now available in", filename

# report some helpful statistics
print "2.5/50/97.5 percentile bonus pool size:", \
    currency_str(numpy.percentile(bonus_pool_outcomes, 2.5)), \
    currency_str(numpy.percentile(bonus_pool_outcomes, 50)), \
    currency_str(numpy.percentile(bonus_pool_outcomes, 97.5))
for month, values in sorted(quarterly_tax_outcomes.iteritems()):
    print "2.5/50/97.5 percentile tax draw in month %d:" % month, \
        currency_str(numpy.percentile(values, 2.5)), \
        currency_str(numpy.percentile(values, 50)), \
        currency_str(numpy.percentile(values, 97.5))
