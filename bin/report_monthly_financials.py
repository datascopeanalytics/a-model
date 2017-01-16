#!/usr/bin/env python
"""
This script is used to quickly create financial summaries that can be imported
into a slack post and shared with the broader team.
"""

import jinja2

from a_model.company import Company
from a_model.argparsers import ReportFinancialsParser

# parse command line arguments
parser = ReportFinancialsParser(description=__doc__)
args = parser.parse_args()

# instantiate company
company = Company(today=args.today)
now = company.profit_loss.get_now()

# margin
ytd_margin = company.profit_loss.get_ytd_margin()
last_ytd_margin = company.profit_loss.get_ytd_margin(year=now.year-1)
ytd_margin_growth = (ytd_margin - last_ytd_margin) / last_ytd_margin

# revenues
ytd_revenue = company.profit_loss.get_ytd_revenue()
last_ytd_revenue = company.profit_loss.get_ytd_revenue(year=now.year-1)
ytd_revenue_growth = (ytd_revenue - last_ytd_revenue) / last_ytd_revenue

# accounts receivable
ar_total = company.ar_aging.get_total()

# TODO invoice projectsions through november


# TODO estimated revenue in this fiscal year


# TODO finalize sales pipeline


# TODO proposal pipeline


# render and report results
env = jinja2.Environment(
    loader=jinja2.PackageLoader('a_model', 'templates'),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)
template = env.get_template('monthly_financials.md')
print template.render(**locals())
