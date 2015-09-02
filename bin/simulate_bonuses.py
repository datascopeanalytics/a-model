#!/usr/bin/env python
"""
Simulate cashflow and estimate how much will be available for each person's
bonus at the end of the year.
"""
import datetime

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter

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
eoy_profit_list = []
for monthly_cash in monthly_cash_outcomes:
    eoy_cash = monthly_cash[months_until_eoy]
    profit = eoy_cash - cash_buffer
    eoy_profit_list.append(profit)


def get_person_bonuses(person, eoy_profit_list):
    bonuses = []
    for profit in eoy_profit_list:
        bonuses.append(max(0, profit * person.net_fraction_of_profits()))
    return bonuses


def get_person_bonus_cdf(person, eoy_profit_list):
    bonuses = get_person_bonuses(person, eoy_profit_list)
    bonuses.sort()
    cdf = [1.0 - float(i)/len(bonuses) for i in range(len(bonuses))]
    return bonuses, cdf


# change the size of the canvas
a, b = plt.rcParams["figure.figsize"]
plt.rcParams["figure.figsize"] = [b, a]

# create a figure for each person
# http://stackoverflow.com/a/29962074/564709
figure = plt.figure()
figure, axes = plt.subplots(len(datascope), sharex=True, sharey=True)
for ax, person in zip(axes, datascope):
    x, y = get_person_bonus_cdf(person, eoy_profit_list)
    ax.plot(x, y, color='#e41a1c', linewidth=2)

    # TODO add line for goal bonuses
    goal = 12 * person.before_tax_target_bonus_dividends()
    ax.plot([goal, goal], [0, 1], color='k', linestyle='--')

    # TODO add line for 1 month salary


# set tick labels to be smaller
tick_label_size = 8
for ax in figure.axes:
    ax.tick_params(axis='both', which='major', labelsize=tick_label_size)

# set the x-axis to be formatted nicely
# http://matplotlib.org/examples/pylab_examples/custom_ticker1.html
formatter = FuncFormatter(utils.thousands_currency_str)
for ax in figure.axes:
    ax.xaxis.set_major_formatter(formatter)

# reduce space between plots and get rid of the tick at 0 to make everything
# compact (only need to do this on one axis since axes are shared)
figure.subplots_adjust(hspace=0)
figure.axes[0].set_ylim(0.01, 1)

# add labels for each person
pad = 0.02
for ax, person in zip(figure.axes, datascope):
    bb = ax.get_position()
    figure.text(
        bb.x1 - pad,
        bb.y1 - pad,
        person.name,
        fontsize=tick_label_size,
        horizontalalignment='right',
        verticalalignment='top',
    )

# add axis labels for the entire grid and make sure they are centered correctly
# http://stackoverflow.com/a/26892326/564709
bb0 = figure.axes[0].get_position()
bb1 = figure.axes[-1].get_position()
ymid = 0.5 * (bb0.y1 + bb1.y0)
xmid = 0.5 * (bb1.x0 + bb1.x1)
figure.text(bb0.x0-0.08, ymid, 'cumulative distribution', va='center',
            rotation='vertical')
figure.text(xmid, bb1.y0-0.05, 'dividends + pre-tax bonus', ha='center')

# save to disk
filename = 'bonuses.png'
plt.savefig(filename)
print "results now available in", filename
