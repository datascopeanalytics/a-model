# NOTE: The quickbooks API is intended for webapps, not for people to download
# their own data. A simple downloading scheme with requests didn't work because
# of some janky ass javascript and iframe bullshit that quickbooks online has.
# Selenium was the best choice.
import os
import sys
import datetime
import time
import itertools
import operator
import json
import re
import csv

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
from dateutil.relativedelta import relativedelta

from .. import utils
from . import exceptions


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

    SLEEPING_TIME = 3  # seconds

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
        # quickbooks will not let you sign in. sleeping after clicking also
        # helps let quickbooks log you into the system before making the next
        # request.
        time.sleep(self.SLEEPING_TIME)
        self.find_element_by_name("SignIn").click()
        time.sleep(self.SLEEPING_TIME)

    def get(self, *args, **kwargs):
        # wrap these GET requests in SLEEPING_TIME to give poor qwuickbwooks
        # some time to rest before asking it for more information.
        time.sleep(self.SLEEPING_TIME)
        result = super(Browser, self).get(*args, **kwargs)
        time.sleep(self.SLEEPING_TIME)


class Cell(object):
    def __init__(self, row, col, value):
        self.row = row
        self.col = col
        try:
            self.value = float(value.replace('$', '').replace(',', ''))
        except:
            self.value = value

    @property
    def colchr(self):
        # TODO: if we ever get past 26*26 columsn, this won't work
        c = ''
        tens = self.col / 26
        zero = ord('A')
        # it goes A AA AB, AC, ... BA BB BC ...
        if tens > 0:
            c += chr(tens + zero - 1)
        c += chr(self.col - tens * 26 + zero)
        return c

    @property
    def excel_coords(self):
        return "%s%s" % (self.colchr, self.row + 1)

    def __repr__(self):
        return '<Cell %s: %s>' % (self.excel_coords, self.value)


class Report(object):
    # TODO: could detect the report and gsheet tab name automatically from the
    # class name for nearly all reports (except ARAging)
    report_name = None
    report_ext = '.csv'
    gsheet_tab_name = None

    # specify whether this is downloaded from 'quickbooks' or 'gdrive' and
    # whether it needs to be uploaded to 'gdrive'
    download_method = None
    upload_method = None

    # parameters for quickbooks url
    # url for quickbooks QUICKBOOKS_ROOT_URL
    start_date = datetime.date(2014, 1, 1)

    def __init__(self, today=None):
        self.end_date = utils.end_of_last_month(today)
        self.filename = os.path.join(
            utils.DATA_ROOT, self.report_name + self.report_ext
        )
        self.cells = []

    def _get_date_customized_params(self):
        return(
            ('date_macro', 'custom'),
            ('customized', 'yes'),
        )

    def get_date_range_customized_params(self):
        return (
            ('high_date', utils.qbo_date_str(self.end_date)),
            ('low_date', utils.qbo_date_str(self.start_date)),
        ) + self._get_date_customized_params()

    def get_report_date_customized_params(self):
        return (
            ('report_date', utils.qbo_date_str(self.end_date)),
        ) + self._get_date_customized_params()

    def get_qbo_query_params(self):
        raise NotImplementedError

    @property
    def url(self):
        """convenience function for creating report urls"""
        report_url = QUICKBOOKS_ROOT_URL + '/app/report'
        return report_url + '?' + utils.urlencode(self.get_qbo_query_params())

    def download_from_quickbooks(self, browser):
        browser.get(self.url)

        # get the HTML out of the report
        try:
            browser.find_element_by_id('legacyframe')
        except NoSuchElementException:
            table_html = ''
            for table in browser.find_elements_by_tag_name('table'):
                table_html += table.get_attribute('innerHTML')
        else:
            iframe = browser.find_element_by_tag_name('iframe')
            browser.switch_to_frame(iframe)
            iframe2 = browser.find_element_by_tag_name('iframe')
            browser.switch_to_frame(iframe2)
            table = browser.find_element_by_id('rptBodyTable')
            table_html = table.get_attribute('innerHTML')
            browser.switch_to_default_content()

        self.extract_table_from_html(table_html)
        self.save_csv()

    def extract_table_from_html(self, table_html):
        soup = BeautifulSoup(table_html, 'html.parser')
        for row, tr in enumerate(soup.find_all('tr')):
            for col, cell in enumerate(tr.find_all(re.compile('td|th'))):
                value = cell.format_string(cell.get_text(), formatter='html')
                value = value.replace('&nbsp;', ' ').strip()
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
        csv_str = google_worksheet.export('csv')
        with open(self.filename, 'w') as output:
            output.write(csv_str)
        print self.filename

    def upload_to_gdrive(self):
        # parse the resulting data from xls and upload it to a google
        # spreadsheet
        self.load_table()
        max_cell = self.get_max_cell()
        excel_dimensions = 'A1:%s' % max_cell.excel_coords

        # clear the google doc contents
        google_worksheet = self.open_google_worksheet()
        not_empty_cells = google_worksheet.findall(re.compile(r'[a-zA-Z0-9]+'))
        for cell in not_empty_cells:
            cell.value = ''
        google_worksheet.update_cells(not_empty_cells)

        # add columns and rows as necessary
        if google_worksheet.col_count <= max_cell.col + 1:
            n_cols = max_cell.col + 1 - google_worksheet.col_count
            google_worksheet.add_cols(n_cols)
        if google_worksheet.row_count <= max_cell.row + 1:
            n_rows = max_cell.row + 1 - google_worksheet.row_count
            google_worksheet.add_rows(n_rows)

        # upload the contents
        google_cell_list = google_worksheet.range(excel_dimensions)
        for google_cell, cell in zip(google_cell_list, self.cells):
            google_cell.value = cell.value
        google_worksheet.update_cells(google_cell_list)

    def add_cell(self, *args):
        self.cells.append(Cell(*args))

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
        self.cells.sort(key=operator.attrgetter('row', 'col'))

    def get_max_cell(self):
        max_cell = Cell(0, 0, None)
        for cell in self.cells:
            if cell.row >= max_cell.row:
                max_cell.row = cell.row
            if cell.col >= max_cell.col:
                max_cell.col = cell.col
        return max_cell

    def _resolve_min_max(self, min_coord, max_coord):
        return min_coord or 0, max_coord or sys.maxint

    def iter_rows(self, min_row=None, max_row=None):
        min_row, max_row = self._resolve_min_max(min_row, max_row)
        self.cells.sort(key=operator.attrgetter('row', 'col'))
        rowgetter = operator.attrgetter('row')
        for row, cells in itertools.groupby(self.cells, rowgetter):
            if min_row <= row <= max_row:
                yield list(cells)

    def _get_row_index(self, row_name, col=0):
        """Get the row index for a row named `row_name` in `col`"""
        if not isinstance(row_name, (str, unicode)):
            raise TypeError('please provide the row_name')
        for cell in self.iter_cells_in_col(col):
            if cell.value == row_name:
                return cell.row
        raise exceptions.RowNotFound(row_name)

    def _get_col_index(self, col_name, row=0):
        """Get the col index for a col named `col_name` in `row`"""
        if not isinstance(col_name, (str, unicode)):
            raise TypeError('please provide the col_name')
        for cell in self.iter_cells_in_row(row):
            if cell.value == col_name:
                return cell.col
        raise exceptions.ColNotFound(col_name)

    def iter_cells_in_row(self, row, min_col=None, max_col=None):
        if isinstance(row, (str, unicode)):
            row = self._get_row_index(row)
        min_col, max_col = self._resolve_min_max(min_col, max_col)
        for cell in self.cells:
            if cell.row == row and (min_col <= cell.col <= max_col):
                yield cell

    def iter_cells_in_col(self, col, min_row=None, max_row=None):
        if isinstance(col, (str, unicode)):
            col = self._get_col_index(col)
        min_row, max_row = self._resolve_min_max(min_row, max_row)
        for cell in self.cells:
            if cell.col == col and (min_row <= cell.row <= max_row):
                yield cell

    def get_historical_values(self, row_name, min_col=1, max_col=None):
        """get all of the historical values from row that starts with
        `row_name`
        """
        historical_values = []
        self.load_table()

        # iterate from min_col to max_col
        max_col = max_col or self.get_max_cell().col
        date_cells = self.iter_cells_in_row(1, min_col, max_col)
        value_cells = self.iter_cells_in_row(row_name, min_col, max_col)
        for date_cell, value_cell in zip(date_cells, value_cells):
            historical_values.append((
                self.get_date_from_cell(date_cell),
                value_cell.value or 0.0,
            ))
        return historical_values

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
        return self.end_date

    def get_months_from_now(self, date):
        now = self.get_now()
        dt = relativedelta(date, now)
        return 12 * dt.years + dt.months

    def get_date_in_n_months(self, n_months):
        t = self.get_now()
        for month in range(n_months):
            t += datetime.timedelta(days=1)
            t = utils.end_of_month(t)
        return t
