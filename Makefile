DATA_DIR = .data
PNG_OUTPUT = \
    cash_in_bank.png \
	bonuses.png \
	hiring_risk.png
CSV_OUTPUT = \
	$(DATA_DIR)/ar_aging.csv \
	$(DATA_DIR)/balance_sheet.csv \
	$(DATA_DIR)/profit_loss.csv \
	$(DATA_DIR)/revenue_projections.csv \
	$(DATA_DIR)/roster.csv \
	$(DATA_DIR)/unpaid_invoices.csv

all: csvs pngs

clean:
	rm -f $(PNG_OUTPUT)

csvs: $(CSV_OUTPUT)
	sync_quickbooks_gdrive.py

pngs: $(PNG_OUTPUT)

cash_in_bank.png:
	simulate_cash_in_bank.py

bonuses.png:
	simulate_bonuses.py

hiring_risk.png:
	simulate_hiring_risk.py
