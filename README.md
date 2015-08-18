There are a lot of levels at which we can try to better understand Datascope's
profitability and ability to grow. For as simple of a concept as
"profitability" is, it is inextricably linked to factors like personal
take-home pay, type of work we do (*poke my eyes out* tasks are less fun), and
amount of time we work. To get a better sense of this, the goal of this model
is to make it easier for everyone to understand how their personal goals are
tied to Datascope's.


## quickstart

1. Create a virtualenv and install the requirements
   ```sh
   mkvirtualenv a-model
   pip install -r requirements/python-dev
   ```

2. Some of the scripts use selenium to download various things. Make sure you
   have the most recent version of Firefox installed. [Upgrade instructions
   here](https://support.mozilla.org/en-US/kb/update-firefox-latest-version).

3. Create a soft link to the `a-model` shared Dropbox folder
   ```sh
   ln -s ~/Dropbox/Library/a-model Dropbox
   ```

4. Run the [`update_budget_spreadsheet.py`](src/update_budget_spreadsheet.py)
   to download the most up-to-date information from quickbooks.

5. Play with the models.

    * [`profitability_and_salary.py`](src/profitability_and_salary.py)
      is useful for understanding the relationship between your desired salary
      and Datascope's profitability.

    * [`hiring_confidence.py`](src/hiring_confidence.py)
      simulates our revenues based on historical data to gauge the risk in
      adding a new person to our team today.

    * [`estimate_bonuses.py`](src/estimate_bonuses.py)
      estimates our bonuses based on current cash in the bank and simulated
      revenues for the remainder of the year.

6. [![Build
   Status](https://travis-ci.org/datascopeanalytics/a-model.svg?branch=master)](https://travis-ci.org/datascopeanalytics/a-model)
   See `.travis.yml` for details on the test suite
