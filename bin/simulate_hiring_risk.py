#!/usr/bin/env python
"""
Simulate cashflow and estimate how risky it is to bring on a Datascoper.
"""

import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from a_model.company import Company
from a_model.argparsers import HiringParser
from a_model import utils
from a_model import decorators

# parse command line arguments
parser = HiringParser(description=__doc__)
args = parser.parse_args()

# instantiate company
company = Company(today=args.today)


# simulate finances in our current situation and by adding up to n_n00bs new
# datascopers
# @decorators.read_or_run
def get_all_n00b_outcomes():
    all_n00b_outcomes = []
    for n00b in range(0, args.n_n00bs+1):
        if n00b > 0:
            company.add_person("n00b_%d" % n00b)
        monthly_cash_outputs, _, _ = company.simulate_monthly_cash(
            n_months=args.n_months,
            n_universes=args.n_universes,
            verbose=args.verbose,
            ontime_payment=args.ontime_payment,
            ontime_completion=args.ontime_completion,
        )

        # create a data structure to store the information in a relevant way
        n00b_outcomes = company.get_outcomes_in_month(0, [])
        all_n00b_outcomes.append(n00b_outcomes)
        for k in n00b_outcomes:
            n00b_outcomes[k] = []

        # calculate the outcomes month by month
        for month in range(args.n_months):
            outcomes = company.get_outcomes_in_month(
                month,
                monthly_cash_outputs,
            )
            for outcome, value in outcomes.iteritems():
                n00b_outcomes[outcome].append(value)
    return all_n00b_outcomes
all_n00b_outcomes = get_all_n00b_outcomes()

# change the canvas to be in portrait instead of landscape to give ourselves
# more vertical space
a, b = plt.rcParams["figure.figsize"]
plt.rcParams["figure.figsize"] = [b, a]

# create a figure for each outcome
figure, axes = plt.subplots(len(all_n00b_outcomes[0]), sharex=True)
time = [t for t in company.iter_future_months(args.n_months)]
for n_n00bs in range(len(all_n00b_outcomes)):

    # configure a few parameters for this particular number of n00bs
    f = float(n_n00bs) / (args.n_n00bs + 1)
    params = {
        'label': '%d n00bs' % n_n00bs,
        'color': plt.cm.YlOrBr(1.0 - f),
        'linewidth': 2 * (1.0 - f) + 1,
        'clip_on': False,
    }
    params['label'] = '%d n00bs' % n_n00bs
    if n_n00bs == 1:
        params['label'] = params['label'][:-1]

    n00b_outcomes = all_n00b_outcomes[n_n00bs]
    for outcome, ax in zip(n00b_outcomes, axes):
        ax.plot(time, n00b_outcomes[outcome], **params)

# set domain of all y-axes so numbers always make sense
for ax in axes:
    ax.set_ylim(0, 1)

# add y-axis labels
for outcome, ax in zip(all_n00b_outcomes[0], axes):
    ax.set_ylabel(outcome)

# format x-axes. only need to do this once since sharex=True
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
plt.gcf().autofmt_xdate()

# clean up each individual graph
# http://stackoverflow.com/a/28720127/564709
for ax in axes:
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for tic in ax.xaxis.get_major_ticks():
        tic.tick1On = tic.tick2On = False
    for tic in ax.yaxis.get_major_ticks():
        tic.tick2On = False

# TODO add line at end of year

# add legend
axes[0].legend(fontsize=8, frameon=False)

# save to disk
filename = 'hiring_risk.png'
plt.savefig(filename)
print "results now available in", filename
