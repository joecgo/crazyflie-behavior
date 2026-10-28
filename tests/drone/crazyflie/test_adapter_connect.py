"""The Crazyflie adapter's connect(), against a fake cflib.

pytest's monkeypatch swaps the adapter's cflib classes for fakes for one test,
then puts the real ones back.
"""

# pyright: reportPrivateUsage=false

from unittest.mock import MagicMock

import pytest

from crazyflie_behavior.drone.crazyflie import adapter as adapter_module
from crazyflie_behavior.drone.crazyflie.adapter import CrazyflieAdapter
from crazyflie_behavior.snapshot import RangeStatus
from crazyflie_behavior.timing.clock import SimClock


class FakeCflib:
    """Stands in for cflib during connect(): records what the adapter asked for."""

    def __init__(self) -> None:
        self.link = MagicMock()
        """The SyncCrazyflie: open_link, close_link, and the Crazyflie as .cf."""
        self.parameters = {"deck.bcFlow2": "1", "deck.bcMultiranger": "0"}
        """Parameter values as cflib returns them (strings). Missing means the
        firmware doesn't know the parameter, so cflib raises KeyError."""
        self.link.cf.param.get_value.side_effect = self.get_parameter
        self.reset_estimator = MagicMock()
        self.log_block_names: list[str] = []
        self.log_block_periods_ms: dict[str, int] = {}

    def get_parameter(self, name: str) -> str:
        return self.parameters[name]

    def make_log_block(self, name: str, period_in_ms: int) -> MagicMock:
        self.log_block_names.append(name)
        self.log_block_periods_ms[name] = period_in_ms
        return MagicMock()


@pytest.fixture
def fake_cflib(monkeypatch: pytest.MonkeyPatch) -> FakeCflib:
    fake = FakeCflib()
    monkeypatch.setattr(adapter_module, "_drivers_initialized", True)
    monkeypatch.setattr(adapter_module, "SyncCrazyflie", MagicMock(return_value=fake.link))
    monkeypatch.setattr(adapter_module, "Crazyflie", MagicMock())
    monkeypatch.setattr(adapter_module, "reset_estimator", fake.reset_estimator)
    monkeypatch.setattr(adapter_module, "LogConfig", fake.make_log_block)
    return fake


@pytest.fixture
def adapter() -> CrazyflieAdapter:
    return CrazyflieAdapter(SimClock(start=10.0))


def test_connecting_resets_the_estimate_and_starts_telemetry(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()

    fake_cflib.reset_estimator.assert_called_once_with(fake_cflib.link)
    assert fake_cflib.log_block_names == ["state", "battery", "down"]
    fake_cflib.link.close_link.assert_not_called()


def test_a_multi_ranger_adds_its_own_log_block(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.parameters["deck.bcMultiranger"] = "1"

    adapter.connect()

    assert "multiranger" in fake_cflib.log_block_names


def test_log_periods_are_ones_the_firmware_accepts(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.parameters["deck.bcMultiranger"] = "1"

    adapter.connect()

    for period_ms in fake_cflib.log_block_periods_ms.values():
        assert 10 <= period_ms <= 2540  # the firmware counts periods in 10 ms steps
        assert period_ms % 10 == 0
    # The firmware reads the Multi-ranger every 100 ms (ADR-0022); faster only repeats.
    assert fake_cflib.log_block_periods_ms["multiranger"] >= 100


def test_without_a_multi_ranger_its_directions_read_invalid_never_clear(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    adapter.connect()

    readings = adapter._telemetry.snapshot(10.0, 0.0).range_readings
    for reading in (readings.front, readings.back, readings.left, readings.right, readings.up):
        assert reading is not None
        assert reading.value.status is RangeStatus.INVALID


def test_the_older_flow_deck_counts_too(adapter: CrazyflieAdapter, fake_cflib: FakeCflib) -> None:
    del fake_cflib.parameters["deck.bcFlow2"]  # firmware without the v2 parameter
    fake_cflib.parameters["deck.bcFlow"] = "1"

    adapter.connect()

    fake_cflib.reset_estimator.assert_called_once()


def test_without_a_flow_deck_it_refuses_to_fly_and_closes_the_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.parameters["deck.bcFlow2"] = "0"

    with pytest.raises(RuntimeError, match="Flow deck"):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()
    fake_cflib.reset_estimator.assert_not_called()


def test_any_failing_setup_step_closes_the_link(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.reset_estimator.side_effect = TimeoutError("estimate never settled")

    with pytest.raises(TimeoutError):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()


def test_a_missing_log_variable_says_to_update_the_firmware(
    adapter: CrazyflieAdapter, fake_cflib: FakeCflib
) -> None:
    fake_cflib.link.cf.log.add_config.side_effect = KeyError("Variable supervisor.info not in TOC")

    with pytest.raises(RuntimeError, match="Update the firmware"):
        adapter.connect()

    fake_cflib.link.close_link.assert_called_once()
