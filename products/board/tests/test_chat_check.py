"""Ruling 122's record outside the code, pure: the unit names the chat
model's address and model, the spec's jobs line says the chat pane alone
calls a model, and check item 28 asks the brief's question within 30 s and
says "model not running, chat item skipped" rather than failing."""
import os
import re

from products.board import chat, check

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_unit_names_the_chat_address_and_model():
    unit = open(os.path.join(HERE, "units", "qv4-board.service"), encoding="utf-8").read()
    env = dict(re.findall(r"(QV4_CHAT_\w+)=(\S+)", unit))
    assert env == {"QV4_CHAT_URL": "http://127.0.0.1:8060/v1/chat/completions", "QV4_CHAT_MODEL": "qwen4exp"}
    assert chat.LANE == "board-chat"


def test_the_spec_says_the_chat_pane_alone_calls_a_model():
    spec = open(os.path.join(HERE, "spec.md"), encoding="utf-8").read()
    jobs = next(line for line in spec.splitlines() if line.startswith("jobs:"))
    assert "no capture, no fetch; the chat pane alone calls the chat model through support.modelclient" in jobs
    assert "no model" not in jobs
    assert "POST /chat" in spec and all(f"`{t}`" in spec for t in ("registers", "search", "row", "dossier"))
    assert "QV4_CHAT_URL" in spec and "QV4_CHAT_MODEL" in spec


def test_check_item_28_asks_within_30_s_and_skips_without_the_model():
    assert check.CHAT_QUESTION == "which registers hold Rank Group Limited?" and check.CHAT_FLOOR_S == 30.0
    src = open(check.__file__, encoding="utf-8").read()
    assert "model not running, chat item skipped" in src and "out += chat_problems(conn)" in src
    port = check.closed_port()
    assert 0 < port < 65536
