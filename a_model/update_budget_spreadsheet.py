"""
This script is used to download data directly from quickbooks and cache the
results locally.
"""
# NOTE: The quickbooks API is intended for webapps, not for people to download
# their own data. A simple downloading scheme with requests didn't work because
# of some janky ass javascript and iframe bullshit that quickbooks online has.
# Selenium was the best choice.

import urlparse
import time
import os
import datetime
import itertools
import glob

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import gspread
import openpyxl

from datascope import Datascope
import utils

# url for quickbooks homepage
homepage = 'http://qbo.intuit.com'


def get_report_url(params):
    """convenience function for creating report urls"""
    report_url = homepage + '/app/report'
    return report_url + '?' + utils.urlencode(params)

# prepare a bunch of urls for accessing different reports
start_date = datetime.date(2014, 1, 1)
end_date = utils.end_of_last_month()
date_customized_params = (
    ('high_date', utils.qbo_date_str(end_date)),
    ('low_date', utils.qbo_date_str(start_date)),
    ('date_macro', 'custom'),
    ('customized', 'yes'),
)
profit_loss_params = (
    ('rptId', 'reports/ProfitAndLossReport'),
    ('column', 'monthly'),
) + date_customized_params
ar_aging_params = (
    ('rptId', 'AR_AGING'),
    ('report_date', utils.qbo_date_str(end_date)),
    ('date_macro', 'custom'),
    ('customized', 'yes'),
)
balance_sheet_params = (
    ('rptId', 'reports/BalanceSheetReport'),
    ('token', 'BAL_SHEET'),
    ('column', 'monthly'),
    ('collapse_subs', 'true'),
) + date_customized_params
unpaid_invoices_params = (
    ('rptId', 'txreports/TxListReport'),
    ('arpaid', '2'),
    ('token', 'INVOICE_LIST'),
) + date_customized_params
profit_loss_url = get_report_url(profit_loss_params)
ar_aging_url = get_report_url(ar_aging_params)
balance_sheet_url = get_report_url(balance_sheet_params)
unpaid_invoices_url = get_report_url(unpaid_invoices_params)

# instantiate the datascope object
datascope = Datascope()

# basic filename manipulation
profit_loss_filename = datascope.profit_loss.filename
ar_aging_filename = datascope.ar_aging.filename
balance_sheet_filename = datascope.balance_sheet.filename
unpaid_invoices_filename = datascope.unpaid_invoices.filename


def open_browser():

    excel_mimetypes = (
        'application/vnd.ms-excel',
        'application/msexcel',
        'application/x-msexcel',
        'application/x-ms-excel',
        'application/x-excel',
        'application/x-dos_ms_excel',
        'application/xls',
        'application/x-xls',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

    # create a firefox profile to automatically download files (like excel
    # files) without having to approve of the download
    # http://bit.ly/1WeZziv
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", utils.DATA_ROOT)
    profile.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        ','.join(excel_mimetypes)
    )

    # instantiate a firefox instance and implicitly wait for find_element_*
    # methods for 10 seconds in case content does not immediately appear
    browser = webdriver.Firefox(firefox_profile=profile)
    browser.implicitly_wait(10)
    return browser


# login to quickbooks
def login(browser):
    browser.get(homepage)
    login = browser.find_element_by_name("login")
    login.send_keys(datascope.config.get('quickbooks', 'username'))
    password = browser.find_element_by_name("password")
    password.send_keys(datascope.config.get('quickbooks', 'password'))
    button = browser.find_element_by_id("LoginButton")
    button.click()


def download_report(browser, report_url, xlsx_filename):
    # remove all of the old report*.xlsx crappy filenames that quickbooks
    # creates by default
    report_xlsx_regex = os.path.join(utils.DATA_ROOT, 'report*.xlsx')
    for filename in glob.glob(report_xlsx_regex):
        os.remove(filename)

    # go to the P&L page and download the report locally
    browser.get(report_url)
    iframe = browser.find_element_by_tag_name('iframe')
    browser.switch_to_frame(iframe)
    iframe2 = browser.find_element_by_tag_name('iframe')
    browser.switch_to_frame(iframe2)
    xlsx_export = browser.find_element_by_css_selector('option[value=xlsx]')
    xlsx_export.click()
    browser.switch_to_default_content()

    # check to see if the file has been downloaded
    while not glob.glob(report_xlsx_regex):
        time.sleep(1)
    qbo_xlsx_filename = glob.glob(report_xlsx_regex)[0]
    os.rename(qbo_xlsx_filename, xlsx_filename)


def upload_report_to_google(xlsx_filename, gsheet_tab_name):

    # parse the resulting data from xlsx and upload it to a google spreadsheet
    excel_workbook = openpyxl.load_workbook(xlsx_filename)
    excel_worksheet = excel_workbook.active
    pl_dimension = excel_worksheet.calculate_dimension()
    excel_row_list = excel_worksheet.range(pl_dimension)
    excel_cell_list = itertools.chain(*excel_row_list)

    google_workbook = datascope.open_google_workbook()
    google_worksheet = google_workbook.worksheet(gsheet_tab_name)
    google_cell_list = google_worksheet.range(pl_dimension)

    for google_cell, excel_cell in zip(google_cell_list, excel_cell_list):
        if excel_cell.value is None:
            google_cell.value = ''
        else:
            google_cell.value = excel_cell.value
    google_worksheet.update_cells(google_cell_list)


def sync_quickbooks_to_google(browser, report_url, xlsx_filename, tab_name):
    """
    Convenience method for syncing a report in quickbooks to google spreadsheet
    """
    download_report(browser, report_url, xlsx_filename)
    upload_report_to_google(xlsx_filename, tab_name)


if __name__ == '__main__':
    browser = open_browser()
    login(browser)

    # sync quickbooks report to google spreadsheet
    sync_quickbooks_to_google(
        browser, profit_loss_url, profit_loss_filename, "P&L",
    )
    sync_quickbooks_to_google(
        browser, ar_aging_url, ar_aging_filename, "A/R Aging",
    )
    sync_quickbooks_to_google(
        browser, balance_sheet_url, balance_sheet_filename, "Balance Sheet",
    )

    # download the unpaid invoices report from quickbooks, which is used in
    # revenue projection simulations later
    download_report(
        browser, unpaid_invoices_url, unpaid_invoices_filename,
    )

    # close the browser
    browser.close()
