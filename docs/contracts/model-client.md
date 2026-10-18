# Contract: the model client

**Fixes:** how any code calls a model. **Test:**
`support/modelclient/tests/`. **Taken from:**
`data-layer/modelgate/modelgate/client.py`, with refusal on for every lane
(it recorded a wrong model in 13.8% of one lane's calls and carried on).

1. **Every call names its model,** and an answer from a different model is
   refused and discarded, for every lane. There is no lenient lane. This
   holds for `chat` and for `embed` alike (the old client's embedding call
   never checked). What answered is READ BACK from the server's model list
   where the answer cannot say: an embeddings answer's `model` field is the
   request echoed, a chat answer's is the server's own name.
2. **Local addresses only:** the loopback, the two boxes and the floating
   address. Any other host is refused before a byte leaves (hard limit 10).
3. **Every call is recorded** in the calls ledger: the lane, the model
   asked for and served, the address, token counts, seconds, and any
   refusal or error. The ledger never holds the prompt, the texts or the
   answer. An embedding call records how many texts and their characters;
   a short answer (fewer vectors than texts) is an error, never a gap.
4. **After step 2, every call goes through the scheduler,** which places it
   on a model profile; the client is what the scheduler's workers use.
5. **The review agent's web search** (track C) is not a model call and has
   its own limits (hard limits 12 and 26).
