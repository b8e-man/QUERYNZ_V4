# Whether the first full copy of the charities feed runs by day, now, or on the job's first night
default: The first night after the merge. The brief says off-peak; at 07:30 this was not off-peak, so this session landed only a proof (24 requests: the documents about the feed, the code lists, Groups whole, two pages of Organisations). The rest, about 1,170 requests and two hours, waits for 23:30.
blocks: The measure against the register's count of registered charities, and both builds of the reading (charities_a, charities_b), until the copy is held.
recommendation: The default. If you want it sooner, run on node2, in /home/user/querynzv4 after the merge: `nice -n 10 .venv/bin/python -m registers.charities.capture --anytime --budget-s 14400`, then `.venv/bin/python -m registers.charities.capture --measure`.
raised: 2026-10-20 by charities-capture
