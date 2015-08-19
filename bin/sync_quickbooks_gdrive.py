#!/usr/bin/env python
"""
This script is used to download data directly from quickbooks and cache the
results locally and also synchronoze relevant reports to our google
spreadsheet.
"""

from a_model import reports
from a_model.datascope import Datascope

# get some credentials from the datascope object
datascope = Datascope()
username = datascope.config.get('quickbooks', 'username')
password = datascope.config.get('quickbooks', 'password')

# download and sync the reports
# reports.cache_quickbooks_locally(username, password)
reports.sync_local_cache_with_gdrive()
