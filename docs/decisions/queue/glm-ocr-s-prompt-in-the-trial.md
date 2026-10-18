# Which prompt GLM-OCR runs under in the trial: the old estate's "OCR" or its model card's "Text Recognition:"
default: "OCR", the bare instruction ggml-org's guide uses and the old estate's readings were made with, so pass one reproduces them and the incumbent is judged as it actually ran. Built on this default.
blocks: Nothing. The model card's documented prompt ("Text Recognition:", and "Table Recognition:" for a table page) is recorded in `support/trials/readers.py` as a variant and can be run as one more setting over the same page set after pass two, keyed apart by its prompt hash.
recommendation: The default for the trial's verdict; then run the card's prompt as a variant, because step 3.2 says each model does best on its own documented prompt and the incumbent should not be the one model denied that.
raised: 2026-10-18 by trial
