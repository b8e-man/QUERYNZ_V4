Spot-check a new model on a lane with a throwaway `support.reader.Store` and never `piece()`, so no trial reading reaches the live store, and compare name overlap in both directions.
area: model trials, reader store, lanes, spot checks
paid-for-by: 26 November 2026, Qwen 3.8 27B against Flash-Next on six lanes, 10 documents each

The overlap in both directions says what kind of difference it is: the 27B's names were 90%+ inside Flash-Next's (it invents little) while Flash-Next's were 66% inside the 27B's on Hansard (it leaves names out). A single-direction overlap would have read the same gap as either invention or omission. A batch-read lane (Parliament written questions, 16 to a request) read one document at a time is not the same read; say so beside its figure.
