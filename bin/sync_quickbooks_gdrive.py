#!/usr/bin/env python
"""
This script is used to download data directly from quickbooks and cache the
results locally and also synchronoze relevant reports to our google
spreadsheet.
"""

from a_model import reports
from a_model.company import Company
from a_model.argparsers import SyncParser

# parse command line arguments
parser = SyncParser(description=__doc__)
args = parser.parse_args()

# get some credentials from the company object
company = Company(today=args.today, add_people=False)
username = company.config.get('quickbooks', 'username')
password = company.config.get('quickbooks', 'password')

# download and sync the reports
reports.cache_quickbooks_locally(username, password, reports=args.reports)
reports.sync_local_cache_with_gdrive(reports=args.reports)
