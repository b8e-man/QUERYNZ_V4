"""The proxy over a box's per-card model servers (support/scheduler/fanout.py)."""
import http.server
import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from support.scheduler import fanout as F


def _fake(name: str, delay: float = 0.0):
    """A model server that names itself in every answer."""
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, obj, status=200):
            b = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            if self.path.startswith("/metrics"):
                b = f'vllm:generation_tokens_total{{e="{name}"}} 5\n'.encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)
            elif self.path.startswith("/v1/models"):
                self._json({"data": [{"id": "qwen38-27b"}]})
            else:
                self._json({"ok": True})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            time.sleep(delay)
            self._json({"server": name, "echo": body})

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _proxy(backends):
    srv = F.serve(0, backends, log=lambda m: None)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}", srv


def _post(url, obj):
    req = urllib.request.Request(url + "/v1/chat/completions", data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=10).read())


@pytest.fixture
def two():
    a, b = _fake("a"), _fake("b")
    url, p = _proxy([f"http://127.0.0.1:{a.server_address[1]}", f"http://127.0.0.1:{b.server_address[1]}"])
    yield url, a, b
    for s in (a, b, p):
        s.shutdown()


def test_requests_spread_over_both_servers_and_bodies_pass_through(two):
    url = two[0]
    got = [_post(url, {"n": i}) for i in range(6)]
    assert [g["echo"]["n"] for g in got] == list(range(6))
    assert {g["server"] for g in got} == {"a", "b"}


def test_the_model_is_read_back_and_metrics_are_both_servers(two):
    url = two[0]
    assert json.loads(urllib.request.urlopen(url + "/v1/models").read())["data"][0]["id"] == "qwen38-27b"
    m = urllib.request.urlopen(url + "/metrics").read().decode()
    assert 'e="a"' in m and 'e="b"' in m


def test_a_server_that_refuses_is_passed_over_and_the_request_is_not_lost():
    a = _fake("a")
    dead = "http://127.0.0.1:9"             # nothing listens
    url, p = _proxy([dead, f"http://127.0.0.1:{a.server_address[1]}"])
    try:
        assert all(_post(url, {"n": i})["server"] == "a" for i in range(4))
        assert urllib.request.urlopen(url + "/v1/models").status == 200
    finally:
        a.shutdown()
        p.shutdown()


def test_no_server_answering_is_503():
    url, p = _proxy(["http://127.0.0.1:9"])
    try:
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(url + "/v1/models")
        assert e.value.code == 503
    finally:
        p.shutdown()


def test_the_least_busy_server_takes_the_next_request():
    slow, fast = _fake("slow", delay=1.0), _fake("fast")
    url, p = _proxy([f"http://127.0.0.1:{slow.server_address[1]}", f"http://127.0.0.1:{fast.server_address[1]}"])
    try:
        out = []
        ts = [threading.Thread(target=lambda i=i: out.append(_post(url, {"n": i})["server"])) for i in range(2)]
        ts[0].start()
        time.sleep(0.2)
        ts[1].start()
        for t in ts:
            t.join()
        assert sorted(out) == ["fast", "slow"]
    finally:
        for s in (slow, fast, p):
            s.shutdown()


def test_the_pool_orders_by_in_flight_then_refusals_last():
    clock = [0.0]
    pool = F.Pool(["x", "y"], clock=lambda: clock[0])
    pool.take("x")
    assert pool.order()[0] == "y"
    pool.refused("y")
    assert pool.order()[0] == "x"
    clock[0] = F.DOWN_S + 1
    assert pool.order()[0] == "y"
