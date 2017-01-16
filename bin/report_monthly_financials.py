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

# TODO: get the gdrive links from the report instead of adding hard links

# margin
ytd_margin = company.profit_loss.get_ytd_margin()
last_ytd_margin = company.profit_loss.get_ytd_margin(year=now.year-1)
ytd_margin_growth = (ytd_margin - last_ytd_margin) / last_ytd_margin

# revenues
ytd_revenue = company.profit_loss.get_ytd_revenue()
last_ytd_revenue = company.profit_loss.get_ytd_revenue(year=now.year-1)
ytd_revenue_growth = (ytd_revenue - last_ytd_revenue) / last_ytd_revenue

# accounts receivable
total_ar = company.ar_aging.get_total()

# invoice projections through november
total_invoice_projections = company.invoice_projections.get_total()

# total contracted revenue in this fiscal year
if now.month == 12:
    contracted_revenue_year = now.year + 1
    contracted_revenue = total_ar + total_invoice_projections
elif now.month == 11:
    contracted_revenue_year = now.year
    contracted_revenue = ytd_revenue + total_ar
else:
    contracted_revenue_year = now.year
    contracted_revenue = ytd_revenue + total_ar + total_invoice_projections

# TODO finalize sales pipeline


# TODO proposal pipeline


# render and report results
env = jinja2.Environment(
    loader=jinja2.PackageLoader('a_model', 'templates'),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)
template = env.get_template('monthly_financials.md')
print template.render(**locals())
