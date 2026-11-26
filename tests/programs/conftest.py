"""Fixtures shared by the program tests."""

import signal

import pytest

from crazyflie_behavior.drone.interface import DroneInterface
from crazyflie_behavior.programs import bench
from crazyflie_behavior.programs.bench import BenchTickStep
from crazyflie_behavior.recording.recorder import Recorder

GIVE_UP_AFTER_TICKS = 100
"""The bench tick step below reports done after this many ticks, so a broken stop request fails instead of hanging."""


class InterruptSignalOnThirdTick(BenchTickStep):
    """The bench tick step, with the interrupt signal on its third tick: the bench runs until a stop request."""

    def __init__(self, drone: DroneInterface, recorder: Recorder | None = None) -> None:
        super().__init__(drone, recorder)
        self._ticks_run = 0

    def run(self, time: float, dt: float) -> bool:
        done = super().run(time, dt)
        self._ticks_run += 1
        if self._ticks_run == 3:
            signal.raise_signal(signal.SIGINT)
        return done or self._ticks_run >= GIVE_UP_AFTER_TICKS


@pytest.fixture
def bench_interrupted_on_its_third_tick(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bench program gets the interrupt signal on its third tick."""
    monkeypatch.setattr(bench, "BenchTickStep", InterruptSignalOnThirdTick)
