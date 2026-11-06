"""The signed datagrams: a good one arrives; a wrong key, a tampered body and a replay are dropped."""
import json
import socket

from support.takeover import wire

K = b"k" * 40


def pair(key_a=K, key_b=K):
    a = wire.Wire("node1", key_a, ("127.0.0.1", 0))
    b = wire.Wire("voter", key_b, ("127.0.0.1", 0))
    return a, b, b.sock.getsockname()


def test_a_signed_datagram_arrives():
    a, b, addr = pair()
    a.send(addr, {"op": "renew", "box": "node1"})
    got = b.recv(2)
    assert got and got[0] == "node1" and got[1]["op"] == "renew"


def test_a_wrong_key_is_dropped():
    a, b, addr = pair(key_a=b"x" * 40)
    a.send(addr, {"op": "acquire"})
    assert b.recv(0.5) is None


def test_a_tampered_body_is_dropped():
    a, b, addr = pair()
    raw = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    a.send(raw.getsockname() if False else addr, {"op": "renew"})
    assert b.recv(1)
    env = {"m": {"op": "release"}, "s": "node1", "b": a.boot, "n": 99}
    good = a._sig(json.dumps({"m": {"op": "renew"}, "s": "node1", "b": a.boot, "n": 99},
                             sort_keys=True, separators=(",", ":")).encode())
    raw.sendto(json.dumps({"e": env, "h": good}).encode(), addr)
    assert b.recv(0.5) is None


def test_a_replayed_datagram_is_dropped():
    a, b, addr = pair()
    tap = wire.Wire("tap", K, ("127.0.0.1", 0))           # a listener that captures the bytes on the way
    a.send(tap.sock.getsockname(), {"op": "acquire"})
    tap.sock.settimeout(1)
    data, _ = tap.sock.recvfrom(wire.MAX)
    raw = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    raw.sendto(data, addr)
    assert b.recv(1), "the first delivery arrives"
    raw.sendto(data, addr)                                # the same bytes again
    assert b.recv(0.5) is None
