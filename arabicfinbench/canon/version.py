"""The canon version, stamped into every scored result.

Bump on any change to a transform's behaviour, however small. Two results
scored under different canon versions are not comparable, and the stamp is what
makes that checkable instead of remembered.
"""

CANON_VERSION = "0.7.0"
# 0.7.0 - column ordering pads short rows to the table's width instead of
#         declining on ragged input. Declining fired the rule on a rectangular
#         ground truth and skipped a prediction with one uneven row, leaving the
#         sides in different column frames -- symmetric by construction,
#         asymmetric in effect. Also: an empty prediction can no longer be
#         stored as a ranked measurement.
# 0.6.0 - cell metrics (coverage, numeric exactness, null correctness) now
#         compare the tables GriTS paired, not tables zipped by position. No
#         canon transform changed; the stamp still had to move, because the
#         numbers it guards did.
