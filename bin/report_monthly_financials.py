#!/usr/bin/env python
"""
This script is used to quickly create financial summaries that can be imported
into a slack post and shared with the broader team.
"""

import jinja2
env = jinja2.Environment(
    loader=jinja2.PackageLoader('a_model', 'templates'),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)

from a_model.company import Company
from a_model.argparsers import ReportFinancialsParser

# parse command line arguments
parser = ReportFinancialsParser(description=__doc__)
args = parser.parse_args()

# instantiate company
company = Company(today=args.today)

ytd_margin = 10000. # company.profit_loss.get_ytd_margin()
last_ytd_margin = 50000. # company.profit_loss.get_ytd_margin(months=-12)
ytd_margin_growth = (ytd_margin - last_ytd_margin) / last_ytd_margin

# ytd_revenue = company.profit_loss.get_ytd_revenue()
# last_ytd_revenue = company.profit_loss.get_ytd_revenue(months=-12)
# ytd_revenue_growth = (ytd_revenue - last_ytd_revenue) / last_ytd_revenue

template = env.get_template('monthly_financials.md')
print template.render(**locals())
