"""The goal of this script is to figure out when its appropriate to change our
staffing so that we can be reasonably confident we're making a good decision.

TODO: how to reasonably decide when its a good time to hire, just based on our
cash in the bank. probably something to do with ROI
"""

from datascope import Datascope


n_months = 12
n_universes = 1000

# simulate datascope revenues before adding a person
datascope = Datascope()
no_n00b_outcomes, no_n00b_cash = datascope.simulate_finances(
    n_months=n_months,
    n_universes=n_universes,
)

# simulate revenues after adding a person
datascope.add_person("joe")
n00b_outcomes, n00b_cash = datascope.simulate_finances(
    n_months=n_months,
    n_universes=n_universes,
)

keys = set(n00b_outcomes.keys()).union(set(no_n00b_outcomes.keys()))
for key in keys:
    no_n00b = no_n00b_outcomes[key]
    n00b = n00b_outcomes[key]
    print "%30s%10d%10d%10d" % (key, no_n00b, n00b, n00b - no_n00b)
