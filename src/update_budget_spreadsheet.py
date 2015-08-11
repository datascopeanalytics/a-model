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
import utils


# prepare a bunch of urls for accessing different reports
start_date = datetime.date(2014, 1, 1)
end_date = utils.end_of_last_month()
pl_query_dict = {
    'rptId': 'reports/ProfitAndLossReport',
    'column': 'monthly',
    'date_macro': 'custom',
    'customized': 'yes',
    'low_date': utils.qbo_date_str(start_date),
    'high_date': utils.qbo_date_str(end_date),
}
homepage = 'http://qbo.intuit.com'
report_url = homepage + '/app/report'
pl_report_url = report_url + '?' + urllib.urlencode(pl_query_dict)

# instantiate the datascope object
datascope = Datascope()
download_dir = datascope.data_root

# create a firefox profile to automatically download files (like excel files)
# without having to approve of the download
# http://bit.ly/1WeZziv
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

# instantiate a firefox instance and implicitly wait for find_element_* methods
# for 10 seconds in case content does not immediately appear
browser = webdriver.Firefox(firefox_profile=profile)
browser.implicitly_wait(10)

# login to quickbooks
browser.get(homepage)
login = browser.find_element_by_name("login")
login.send_keys(datascope.config.get('quickbooks', 'username'))
password = browser.find_element_by_name("password")
password.send_keys(datascope.config.get('quickbooks', 'password'))
button = browser.find_element_by_id("LoginButton")
button.click()

# go to the P&L page and download the report locally
browser.get(pl_report_url)
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
