Start a model server with ONE card filter (HIP_VISIBLE_DEVICES alone): with ROCR_VISIBLE_DEVICES set too the card list is filtered twice, nothing is left, and llama-server runs on the processor while answering with the right model name.
area: scheduler, model serving, graphics cards

Seen 18 October 2026 on node2: the first swap loaded the text-reader profile in 12 s, the card's memory never moved, and the server log said "failed to initialize ROCm: no ROCm-capable device is detected". The model name read back was right, so the served-model check passed; only the card's memory and the log told the truth. Check the card's memory after a load, not only the name it answers with.
