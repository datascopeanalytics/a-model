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

2. Get a copy of `config.ini` from @deanmalmgren and put it in the root of this
   repository and edit at will.

3. Play with the models.

    * [`profitability_and_salary.py`](src/profitability_and_salary.py)
      is useful for understanding the relationship between your desired salary
      and Datascope's profitability.

    * [`hiring_confidence.py`](src/profitability_and_salary.py)
      simulates our revenues based on historical data to gauge the risk in
      adding a new person to our team today.
