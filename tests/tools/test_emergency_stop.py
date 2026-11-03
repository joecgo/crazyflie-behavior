"""The emergency-stop script (ADR-0038), against a fake radio link.

tools/ isn't a package that project code or tests import, so the script is
loaded from its path.
"""

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
        (call.args[0].port, call.args[0].channel, bytes(call.args[0].data)) for call in fake_link.send_packet.mock_calls
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

    script.cflib.crtp.get_link_driver.assert_called_once_with(DEFAULT_URI)
    assert not hasattr(script, "Crazyflie")
    assert not hasattr(script, "SyncCrazyflie")


def test_its_default_uri_is_the_adapters(script: ModuleType) -> None:
    assert script.DEFAULT_URI == DEFAULT_URI
