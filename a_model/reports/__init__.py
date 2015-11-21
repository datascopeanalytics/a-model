from base import Browser
from ar_aging import ARAging
from balance_sheet import BalanceSheet
from profit_loss import ProfitLoss
from unpaid_invoices import UnpaidInvoices
from revenue_projections import RevenueProjections


def cache_quickbooks_locally(username, password):
    """Download data from various locations"""

    # these things all come from quickbooks and require selenium
    with Browser() as browser:
        browser.login_quickbooks(username, password)
        ARAging().download_from_quickbooks(browser)
        BalanceSheet().download_from_quickbooks(browser)
        ProfitLoss().download_from_quickbooks(browser)
        UnpaidInvoices().download_from_quickbooks(browser)

    # this is manually entered in a google spreadsheet
    RevenueProjections().download_from_gdrive()


def sync_local_cache_with_gdrive():
    """We only need to upload these reports to Google Drive"""
    ARAging().upload_to_gdrive()
    BalanceSheet().upload_to_gdrive()
    ProfitLoss().upload_to_gdrive()
