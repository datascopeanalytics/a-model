from base import Browser
from ar_aging import ARAging
from balance_sheet import BalanceSheet
from profit_loss import ProfitLoss
from unpaid_invoices import UnpaidInvoices


def cache_quickbooks_locally(username, password):
    """Download data from various locations"""

    # these things all come from quickbooks and require selenium
    with Browser() as browser:
        browser.login_quickbooks(username, password)
        ARAging().download(browser)
        BalanceSheet().download(browser)
        ProfitLoss().download(browser)
        UnpaidInvoices().download(browser)

    # # this is manually entered in a google spreadsheet
    # RevenueProjections().download()


def sync_local_cache_with_gdrive():
    ARAging().upload_to_gdrive()
    BalanceSheet().upload_to_gdrive()
    ProfitLoss().upload_to_gdrive()
