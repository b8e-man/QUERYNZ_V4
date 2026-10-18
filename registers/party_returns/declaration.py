"""The declaration reader (a return's printed total and parts, from its text
layer) lives in `support/docread/declaration.py` since 18 October: step 3's
trial reads it as an answer key, and imports run one way (support never
imports a lane). This name stays so the lane reads as before."""
from support.docread.declaration import *  # noqa: F401,F403
from support.docread.declaration import Declaration, amount, figure_after, figure_alone, label_end, part_of, read  # noqa: F401
