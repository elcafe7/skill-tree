"""All tunable learning constants live here."""
INITIAL_CORRECT = 3
SPACED_CORRECT = 3

P_INIT = 0.1
P_TRANSIT = 0.15
P_GUESS = 0.05
P_SLIP = 0.1

UNLOCK_P_KNOWN = 0.95
DELAYED_SUCCESS_HOURS = 24
DEFAULT_LIMIT = 20
RELEARN_GAP = 2  # in-session repeats go after at least this many other items
