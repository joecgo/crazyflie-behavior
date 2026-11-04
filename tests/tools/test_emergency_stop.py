"""The emergency-stop script (ADR-0038), against a fake radio link.

tools/ isn't a package that project code or tests import, so the script is
loaded from its path.
"""

import ast
import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie.adapter import DEFAULT_URI

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "emergency_stop.py"


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("emergency_stop", SCRIPT)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture
def script() -> ModuleType:
    return load_script()


@pytest.fixture
def fake_link(script: ModuleType, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    link = MagicMock()
    monkeypatch.setattr(script.cflib.crtp, "init_drivers", MagicMock())
    monkeypatch.setattr(script.cflib.crtp, "get_link_driver", MagicMock(return_value=link))
    return link


def test_it_sends_both_generations_of_the_emergency_stop_packet_repeatedly(
    script: ModuleType, fake_link: MagicMock
) -> None:
    script.emergency_stop(send_count=3, send_period=0.0)

    sent = [
        (call.args[0].port, call.args[0].channel, bytes(call.args[0].data))
        for call in fake_link.send_packet.call_args_list
    ]
    supervisor_port, localization_port = 9, 6  # cflib's CRTPPort.SUPERVISOR and LOCALIZATION
    assert sent == [(supervisor_port, 1, b"\x03"), (localization_port, 1, b"\x03")] * 3


def test_it_closes_the_link_even_if_sending_fails(script: ModuleType, fake_link: MagicMock) -> None:
    fake_link.send_packet.side_effect = OSError("the radio was unplugged")

    with pytest.raises(OSError, match="unplugged"):
        script.emergency_stop(send_count=3, send_period=0.0)

    fake_link.close.assert_called_once()


def test_it_says_so_when_the_uri_has_no_link_driver(script: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(script.cflib.crtp, "init_drivers", MagicMock())
    monkeypatch.setattr(script.cflib.crtp, "get_link_driver", MagicMock(return_value=None))

    with pytest.raises(RuntimeError, match="No link driver"):
        script.emergency_stop("nonsense://0")


def test_it_opens_nothing_but_the_radio_link(script: ModuleType, fake_link: MagicMock) -> None:
    # No full connection: no parameters, no decks, no estimate reset, no Crazyflie object.
    script.emergency_stop(send_count=1, send_period=0.0)

    script.cflib.crtp.get_link_driver.assert_called_once()
    assert script.cflib.crtp.get_link_driver.call_args.args == (DEFAULT_URI,)
    assert not hasattr(script, "Crazyflie")
    assert not hasattr(script, "SyncCrazyflie")


def test_its_default_uri_is_the_adapters(script: ModuleType) -> None:
    assert script.DEFAULT_URI == DEFAULT_URI


def test_it_reports_success_only_if_the_radio_took_every_packet(script: ModuleType, fake_link: MagicMock) -> None:
    fake_link.send_packet.return_value = True

    assert script.emergency_stop(send_count=2, send_period=0.0) is True


def test_a_radio_that_does_not_deliver_is_reported_at_the_first_failure_not_after_the_rest(
    script: ModuleType, fake_link: MagicMock
) -> None:
    # cflib's send_packet waits 2 s for a free slot, then returns False: don't wait that long 20 times.
    fake_link.send_packet.return_value = False

    assert script.emergency_stop(send_count=10, send_period=0.0) is False
    assert fake_link.send_packet.call_count == 1
    fake_link.close.assert_called_once()


def test_a_link_error_means_the_stop_is_not_confirmed(script: ModuleType, fake_link: MagicMock) -> None:
    def link_driver(_uri: str, link_error_callback: object) -> MagicMock:
        assert callable(link_error_callback)
        link_error_callback("Too many packets lost")
        return fake_link

    script.cflib.crtp.get_link_driver.side_effect = link_driver

    assert script.emergency_stop(send_count=1, send_period=0.0) is False


def test_main_says_not_confirmed_and_exits_1_when_nothing_was_delivered(
    script: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(script, "emergency_stop", MagicMock(return_value=False))

    exit_code = script.main([])

    assert exit_code == 1
    error_output = capsys.readouterr().err
    assert "NOT CONFIRMED" in error_output
    assert "Run it again" in error_output
    assert "keeping clear of the drone" in error_output


def test_main_names_both_causes_of_a_stop_that_is_not_confirmed(
    script: ModuleType, fake_link: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    # Every packet taken, but a link error on the way: the stop may well have arrived, so the
    # message must not say the radio delivered nothing (REVIEW.md: the stated cause holds on every path).
    def link_driver(_uri: str, link_error_callback: object) -> MagicMock:
        assert callable(link_error_callback)
        link_error_callback("Too many packets lost")
        return fake_link

    fake_link.send_packet.return_value = True
    script.cflib.crtp.get_link_driver.side_effect = link_driver

    assert script.main([]) == 1
    error_output = capsys.readouterr().err
    assert "didn't take every packet" in error_output
    assert "link error" in error_output


def test_main_exits_0_when_the_radio_took_every_packet(
    script: ModuleType, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(script, "emergency_stop", MagicMock(return_value=True))

    assert script.main(["--uri", "radio://0/60/2M"]) == 0
    assert "radio://0/60/2M" in capsys.readouterr().out


def test_the_script_imports_no_project_code_so_a_bug_elsewhere_cant_stop_it() -> None:
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(ast.parse(SCRIPT.read_text(encoding="utf-8")))
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(ast.parse(SCRIPT.read_text(encoding="utf-8")))
        if isinstance(node, ast.ImportFrom)
    }

    assert "cflib" in imported  # the scan sees real imports
    assert "crazyflie_behavior" not in imported
