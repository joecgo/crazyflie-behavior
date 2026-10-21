import pytest

from crazyflie_behavior.timing.clock import RealClock, SimClock


def test_sim_clock_only_moves_when_told_to() -> None:
    clock = SimClock(start=5.0)

    assert clock.now() == 5.0
    clock.advance(0.25)
    assert clock.now() == pytest.approx(5.25)


def test_sim_clock_sleep_jumps_straight_to_the_deadline() -> None:
    clock = SimClock()

    clock.sleep_until(30.0)  # a 30-second wait, instantly

    assert clock.now() == 30.0


def test_sim_clock_sleep_until_a_past_deadline_does_nothing() -> None:
    clock = SimClock(start=10.0)

    clock.sleep_until(4.0)

    assert clock.now() == 10.0


def test_sim_clock_cannot_go_backward() -> None:
    clock = SimClock()

    with pytest.raises(ValueError, match="backward"):
        clock.advance(-1.0)


def test_real_clock_sleeps_until_the_deadline() -> None:
    clock = RealClock()
    deadline = clock.now() + 0.02

    clock.sleep_until(deadline)

    assert clock.now() >= deadline
