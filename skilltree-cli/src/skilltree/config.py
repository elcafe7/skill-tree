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

# Prerequisite mastery (unlock rule)
MASTERY_ITEM_FRACTION = 0.8      # share of a skill's items that must be individually mastered
DELAYED_ITEM_SUCCESSES = 2       # correct answers on distinct study days, each >= DELAYED_SUCCESS_HOURS after item's first exposure
