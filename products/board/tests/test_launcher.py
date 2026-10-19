"""The desktop launcher parses, opens the board through the folder's own
script, and never carries a credential; the unit carries the qv4- prefix."""
import configparser
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESKTOP = os.path.join(HERE, "qv4-board.desktop")
UNIT = os.path.join(HERE, "units", "qv4-board.service")


def test_the_desktop_file_parses_with_name_icon_and_exec():
    cp = configparser.ConfigParser(interpolation=None)
    cp.optionxform = str
    cp.read(DESKTOP, encoding="utf-8")
    e = cp["Desktop Entry"]
    assert e["Type"] == "Application" and e["Name"] and e["Icon"]
    assert e["Exec"] == "/home/user/querynzv4/products/board/open"
    assert e["Terminal"] == "false"


def test_desktop_file_validate_agrees_where_installed():
    if not shutil.which("desktop-file-validate"):
        return
    p = subprocess.run(["desktop-file-validate", DESKTOP], capture_output=True, text=True)
    assert p.returncode == 0 and p.stdout.strip() == "", p.stdout + p.stderr


def test_the_open_script_starts_the_unit_then_opens_the_address():
    s = open(os.path.join(HERE, "open"), encoding="utf-8").read()
    assert os.access(os.path.join(HERE, "open"), os.X_OK)
    assert "systemctl --user start qv4-board.service" in s and "xdg-open" in s and "8420" in s
    for word in ("password", "postgres://", "postgresql://"):
        assert word not in s


def test_the_unit_is_a_qv4_standing_service_on_the_main_checkout():
    u = open(UNIT, encoding="utf-8").read()
    assert os.path.basename(UNIT).startswith("qv4-")
    assert "WorkingDirectory=/home/user/querynzv4\n" in u and "products.board serve" in u
    assert "Restart=on-failure" in u and "QV4_BOARD_PORT=8420" in u
    assert "8300" not in u and "8301" not in u
