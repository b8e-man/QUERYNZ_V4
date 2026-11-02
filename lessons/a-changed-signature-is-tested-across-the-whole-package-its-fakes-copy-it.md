When a function's signature changes, run every test in its package: fakes elsewhere copy the old signature and fail only there.
area: tests, scheduler, fakes, releases

Why: on 3 November 2026 `runner.run` gained `memory_counts`; the runner, registry and policy tests passed and it was released, but `test_chain.py`'s FakeRunner took the old keywords, so four chain tests failed on the released code, and its pin that the MCP pull queues nothing failed on the morning's other change. Found only when the next change ran the folder whole.

How to apply: after changing a signature, grep the tests for fakes of it (`def __call__(self, argv`, `def working_figures(`) and run the whole package's tests, here `support/scheduler/tests/`, before the release.
