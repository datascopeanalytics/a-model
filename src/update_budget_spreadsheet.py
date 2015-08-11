"""
This script is used to download data directly from quickbooks and update our
budget spreadsheet for manual manipulation.
"""
# NOTE: The quickbooks API is intended for webapps, not for people to download
# their own data. A simple downloading scheme with requests didn't work because
# of some janky ass javascript and iframe bullshit that quickbooks online has.
# Selenium was the best choice.

import urlparse
import time
import os
import datetime
import urllib

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from datascope import Datascope


# TODO: make P&L report url a function of a start date and end date
pl_query_dict = {
    'rptId': 'reports/ProfitAndLossReport',
    'column': 'monthly',
    'date_macro': 'custom',
    'customized': 'yes',
    'high_date': '08/10/2015',
    'low_date': '01/01/2014',
}
report_url = 'https://qbo.intuit.com/app/report'
pl_report_url = report_url + '?' + urllib.urlencode(pl_query_dict)
homepage = 'http://qbo.intuit.com'

# instantiate the datascope object
datascope = Datascope()

# create a firefox profile to automatically download files (like excel files)
# without having to approve of the download
# http://bit.ly/1WeZziv
download_dir = os.path.dirname(os.path.abspath(__file__))
profile = webdriver.FirefoxProfile()
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.dir", download_dir)
profile.set_preference(
    "browser.helperApps.neverAsk.saveToDisk",
    ','.join((
        'application/vnd.ms-excel',
        'application/msexcel',
        'application/x-msexcel',
        'application/x-ms-excel',
        'application/x-excel',
        'application/x-dos_ms_excel',
        'application/xls',
        'application/x-xls',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ))
)

# instantiate a firefox instance
browser = webdriver.Firefox(firefox_profile=profile)

# login to quickbooks
browser.get(homepage)
login = browser.find_element_by_name("login")
login.send_keys(datascope.config.get('quickbooks', 'username'))
password = browser.find_element_by_name("password")
password.send_keys(datascope.config.get('quickbooks', 'password'))
button = browser.find_element_by_id("LoginButton")
button.click()

# go to the P&L page and download the report locally
# TODO: detect when elements appear instead of sleeping for 5 seconds
browser.get(pl_report_url)
time.sleep(5)
iframe = browser.find_element_by_tag_name('iframe')
browser.switch_to_frame(iframe)
iframe2 = browser.find_element_by_tag_name('iframe')
browser.switch_to_frame(iframe2)
xlsx_export = browser.find_element_by_css_selector('option[value=xlsx]')
xlsx_export.click()

# TODO: find other way of making sure that the file downloaded correctly
time.sleep(5)
browser.switch_to_default_content()
browser.close()
