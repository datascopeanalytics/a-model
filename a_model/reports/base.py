# NOTE: The quickbooks API is intended for webapps, not for people to download
# their own data. A simple downloading scheme with requests didn't work because
# of some janky ass javascript and iframe bullshit that quickbooks online has.
# Selenium was the best choice.
import os
import sys
import datetime
import glob
import time
import itertools
import operator
import json
import math
import re
import time
import csv

from bs4 import BeautifulSoup
from selenium import webdriver
import gspread
from oauth2client.client import SignedJwtAssertionCredentials

from .. import utils

QUICKBOOKS_ROOT_URL = 'http://qbo.intuit.com'
EXCEL_MIMETYPES = (
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


class Browser(webdriver.Firefox):
    """
    This class is a context manager to be sure to close the browser when we're
    all done.
    """
    def __init__(self, *args, **kwargs):

        # create a firefox profile to automatically download files (like excel
        # files) without having to approve of the download
        # http://bit.ly/1WeZziv
        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference(
            "browser.download.manager.showWhenStarting",
            False,
        )
        profile.set_preference("browser.download.dir", utils.DATA_ROOT)
        profile.set_preference(
            "browser.helperApps.neverAsk.saveToDisk",
            ','.join(EXCEL_MIMETYPES)
        )

        # instantiate a firefox instance and implicitly wait for find_element_*
        # methods for 10 seconds in case content does not immediately appear
        kwargs.update({'firefox_profile': profile})
        super(Browser, self).__init__(*args, **kwargs)
        self.implicitly_wait(30)

    # __enter__ and __exit__ make it a context manager
    # https://code.google.com/p/selenium/issues/detail?id=3228
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def login_quickbooks(self, username, password):
        self.get(QUICKBOOKS_ROOT_URL)
        self.find_element_by_name("Email").send_keys(username)
        self.find_element_by_name("Password").send_keys(password)
        # if you don't wait for a tiny bit before clicking the button,
        # quickbooks will not let you sign in
        time.sleep(3)
        self.find_element_by_name("SignIn").click()


class Cell(object):
    def __init__(self, row, col, value):
        self.row = row
        self.col = col
        try:
            self.value = float(value)
        except:
            self.value = value

    @property
    def colchr(self):
        # TODO: if we ever get past 26*26 columsn, this won't work
        c = ''
        tens = self.col / 26
        zero = ord('A')
        if tens > 0:
            c += chr(tens + zero)
        c += chr(self.col - tens * 26 + zero)
        return c

    @property
    def excel_coords(self):
        return "%s%s" % (self.colchr, self.row + 1)

    def __repr__(self):
        return '<Cell %s: %s>' % (self.excel_coords, self.value)


class Report(object):
    report_name = None
    gsheet_tab_name = None

    # parameters for quickbooks url
    # url for quickbooks QUICKBOOKS_ROOT_URL
    start_date = datetime.date(2014, 1, 1)
    end_date = utils.end_of_last_month()

    def __init__(self):
        self.filename = os.path.join(
            utils.DATA_ROOT, self.report_name
        )
        self.cells = []

    def get_date_customized_params(self):
        return (
            ('high_date', utils.qbo_date_str(self.end_date)),
            ('low_date', utils.qbo_date_str(self.start_date)),
            ('date_macro', 'custom'),
            ('customized', 'yes'),
        )

    def get_qbo_query_params(self):
        raise NotImplementedError

    @property
    def url(self):
        """convenience function for creating report urls"""
        report_url = QUICKBOOKS_ROOT_URL + '/app/report'
        return report_url + '?' + utils.urlencode(self.get_qbo_query_params())

    def download_from_quickbooks(self, browser):
        browser.get(self.url)
        iframe = browser.find_element_by_tag_name('iframe')
        browser.switch_to_frame(iframe)
        iframe2 = browser.find_element_by_tag_name('iframe')
        browser.switch_to_frame(iframe2)
        table = browser.find_element_by_id('rptBodyTable')
        table_html = table.get_attribute('innerHTML')
        self.extract_table_from_html(table_html)
        self.save_csv()
        browser.switch_to_default_content()

    def extract_table_from_html(self, table_html):
        soup = BeautifulSoup(table_html, 'html.parser')
        for row, tr in enumerate(soup.find_all('tr')):
            for col, cell in enumerate(tr.find_all(re.compile('td|th'))):
                value = cell.get_text().encode('ascii', 'ignore')
                value = value.replace('$', '').replace(',', '')
                self.add_cell(row, col, value)

    def save_csv(self):
        with open(self.filename, 'w') as stream:
            writer = csv.writer(stream)
            for row in self.iter_rows():
                writer.writerow([cell.value for cell in row])

    def open_google_workbook(self):
        """Convenience method for opening up the google workbook"""

        # read json from file
        gdrive_credentials = os.path.join(utils.DROPBOX_ROOT, 'gdrive.json')
        with open(gdrive_credentials) as stream:
            key = json.load(stream)

        # authorize with credentials
        credentials = SignedJwtAssertionCredentials(
            key['client_email'],
            key['private_key'],
            ['https://spreadsheets.google.com/feeds'],
        )
        gdrive = gspread.authorize(credentials)

        # open spreadsheet and read all content as a list of lists
        return gdrive.open_by_url(key['url'])

    def open_google_worksheet(self):
        google_workbook = self.open_google_workbook()
        return google_workbook.worksheet(self.gsheet_tab_name)

    def download_from_gdrive(self):
        google_worksheet = self.open_google_worksheet()
        response = google_worksheet.export('csv')
        with open(self.filename, 'w') as output:
            output.write(response.read())
        print self.filename

    def upload_to_gdrive(self):
        # parse the resulting data from xls and upload it to a google
        # spreadsheet
        self.load_table()
        excel_dimensions = self.get_excel_dimensions()

        # clear the google doc contents
        google_worksheet = self.open_google_worksheet()
        not_empty_cells = google_worksheet.findall(re.compile(r'[a-zA-Z0-9]+'))
        for cell in not_empty_cells:
            cell.value = ''
        google_worksheet.update_cells(not_empty_cells)

        # upload the contents
        google_cell_list = google_worksheet.range(excel_dimensions)
        for google_cell, cell in zip(google_cell_list, self.cells):
            google_cell.value = cell.value
        google_worksheet.update_cells(google_cell_list)

    def add_cell(self, *args):
        self.cells.append(Cell(*args))

    def iter_rows(self):
        self.cells.sort(key=operator.attrgetter('row', 'col'))
        rowgetter = operator.attrgetter('row')
        for row, cells in itertools.groupby(self.cells, rowgetter):
            yield list(cells)

    def load_table(self):
        """load the thing into memory in our own format to avoid b.s. with xls
        vs xlsx vs csv formatting
        """
        # save I/O time by exiting if this has already been called. otherwise
        # load in the table
        if self.cells:
            return
        with open(self.filename) as stream:
            reader = csv.reader(stream)
            for row, values in enumerate(reader):
                for col, value in enumerate(values):
                    self.add_cell(row, col, value)

    def get_excel_dimensions(self):
        max_cell = Cell(0, 0, None)
        for cell in self.cells:
            if cell.row >= max_cell.row and cell.col >= max_cell.col:
                max_cell = cell
        return 'A1:%s' % max_cell.excel_coords

    # def _row_cell_range(self, row, min_col, max_col):
    #     return '%(min_col)s%(row)d:%(max_col)s%(row)d' % locals()
    #
    # def _col_cell_range(self, col, min_row, max_row):
    #     return '%(col)s%(min_row)d:%(col)s%(max_row)d' % locals()
    #
    # def iter_cells_in_range(self, cell_range):
    #     for row in self.worksheet.iter_rows(cell_range):
    #         for cell in row:
    #             yield cell
    #

    def iter_cells_in_row(self, row, min_col, max_col=None):
        max_col = max_col or sys.maxint
        for cell in self.cells:
            if cell.row == row and (min_col <= cell.col <= max_col):
                yield cell

    # def iter_cells_in_column(self, col, min_row, max_row):
    #     cell_range = self._col_cell_range(col, min_row, max_row)
    #     return self.iter_cells_in_range(cell_range)
    #
    def get_date_from_cell(self, date_cell):
        if isinstance(date_cell.value, datetime.datetime):
            date = date_cell.value
        else:
            try:
                date = datetime.datetime.strptime(date_cell.value, '%b %Y')
            except ValueError:
                date = utils.qbo_date(date_cell.value)
        return utils.end_of_month(date)

    def get_now(self):
        return utils.end_of_last_month()

    def get_months_from_now(self, date):
        now = self.get_now()
        delta = date - now
        return int(math.floor(delta.days / 30.))

    def get_date_in_n_months(self, n_months):
        t = self.get_now()
        for month in range(n_months):
            t += datetime.timedelta(days=1)
            t = utils.end_of_month(t)
        return t

    # def get_float_from_cell(self, float_cell):
    #     if float_cell.value is None:
    #         return 0.0
    #     elif isinstance(float_cell.value, (float, int, long)):
    #         return float(float_cell.value)
    #     else:
    #         return float(float_cell.value.strip('='))
