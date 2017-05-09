There are a lot of levels at which we can try to better understand Datascope's
profitability and ability to grow. For as simple of a concept as
"profitability" is, it is inextricably linked to factors like personal
take-home pay, type of work we do (*poke my eyes out* tasks are less fun), and
amount of time we work. To get a better sense of this, the goal of this model
is to make it easier for everyone to understand how their personal goals are
tied to Datascope's.


## quickstart

0.  `brew install geckodriver` or `brew upgrade geckodriver`. Make sure you
    are on `geckodriver 0.16.1` or newer. 

1. Create a virtualenv and install the requirements
   ```sh
   mkvirtualenv a-model
   pip install -r requirements/python-dev
   ```

2. Update some environment variables to be able to run the scripts in the `bin`
   directory using the `a_model` python package
   ```sh
   echo 'export PYTHONPATH=`pwd`'     >> ~/.virtualenvs/a-model/bin/postactivate
   echo '__AMODEL_PATH=$PATH'         >> ~/.virtualenvs/a-model/bin/postactivate
   echo 'export PATH=$PATH:`pwd`/bin' >> ~/.virtualenvs/a-model/bin/postactivate
   echo 'unset PYTHONPATH'            >> ~/.virtualenvs/a-model/bin/predeactivate
   echo 'export PATH=$__AMODEL_PATH'  >> ~/.virtualenvs/a-model/bin/predeactivate
   ```
   NOTE: The first time you do this, you will also need to `source
   ~/.virtualenvs/a-model/bin/postactivate` for these changes to take effect
   within your new virtualenv. From here on out though, these bash environment
   variables will be started by default

3. Some of the scripts use selenium to download various things. Make sure you
   have the most recent version of Firefox installed. [Upgrade instructions
   here](https://support.mozilla.org/en-US/kb/update-firefox-latest-version).

4. Create a soft link to the `a-model` shared Dropbox folder, which has various
   credentials you'll need for downloading things.
   ```sh
   ln -s ~/Dropbox/Library/a-model Dropbox
   ```

5. Run the [`sync_quickbooks_gdrive.py`](bin/sync_quickbooks_gdrive.py)
   to download the most up-to-date information from quickbooks. You can also
   sync the data by running `make csvs`

6. Play with the models on an individual basis (see below) or by running
   `make` to generate a bunch of figures at once.

    * [`bin/profitability_and_salary.py`](bin/profitability_and_salary.py)
      is useful for understanding the relationship between your desired salary
      and Datascope's profitability.

    * [`bin/hiring_confidence.py`](bin/hiring_confidence.py)
      simulates our revenues based on historical data to gauge the risk in
      adding a new person to our team today.

    * [`bin/estimate_bonuses.py`](bin/estimate_bonuses.py)
      estimates our bonuses based on current cash in the bank and simulated
      revenues for the remainder of the year.

    * [`bin/simulate_cash_in_bank.py`](bin/simulate_cash_in_bank.py) simulates
      our cash in the bank over the next 12 months

7. [![Build
   Status](https://travis-ci.org/datascopeanalytics/a-model.svg?branch=master)](https://travis-ci.org/datascopeanalytics/a-model)
   See `.travis.yml` for details on the test suite
