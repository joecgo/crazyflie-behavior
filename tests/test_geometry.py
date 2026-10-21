from crazyflie_behavior.geometry import Vector3


def test_vectors_add_and_subtract_per_axis() -> None:
    a = Vector3(1.0, 2.0, 3.0)
    b = Vector3(0.5, -1.0, 2.0)

    assert a + b == Vector3(1.5, 1.0, 5.0)
    assert a - b == Vector3(0.5, 3.0, 1.0)


def test_scaling_a_velocity_by_time_gives_a_displacement() -> None:
    velocity = Vector3(0.2, 0.0, -0.1)

    assert velocity * 2.0 == Vector3(0.4, 0.0, -0.2)
