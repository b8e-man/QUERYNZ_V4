When two standing servers share one port by schedule, drain the outgoing views' pieces on the box before the stop: Radiance answers a request naming the other model, so the reading is stored under the wrong model.
area: scheduler, standing servers, cards.py shift_tick, model serving, reader store
paid-for-by: 26 November 2026, the scheduled swap of Qwen 3.8 27B (by day) and Flash-Next (node2 by night) on :8060

Radiance echoes the model a request names (radiance-echoes-the-model-a-chat-call-asks-for.md), so a Flash-Next view's piece still in flight when the 27B comes up on the same port gets a 27B answer labelled qwen4exp, and the reader stores it under Flash-Next's key. `shift_tick` marks the box's cards draining (a pieced row then starts no new piece and gives its row back), waits until no piece of the outgoing views runs here, and only then stops the unit. A test mutates the wait away and fails (test_standing_schedule.py).
