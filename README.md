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
   pip install -r requirements/python
   ```

2. Create a soft link to the `a-model` shared Dropbox folder
   ```sh
   ln -s ~/Dropbox/Library/a-model Dropbox
   ```

3. Play with the models.

    * [`profitability_and_salary.py`](src/profitability_and_salary.py)
      is useful for understanding the relationship between your desired salary
      and Datascope's profitability.

    * [`hiring_confidence.py`](src/hiring_confidence.py)
      simulates our revenues based on historical data to gauge the risk in
      adding a new person to our team today.

    * [`estimate_bonuses.py`](src/estimate_bonuses.py)
      estimates our bonuses based on current cash in the bank and simulated
      revenues for the remainder of the year.
