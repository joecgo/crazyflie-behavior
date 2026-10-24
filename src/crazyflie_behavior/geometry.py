"""Geometry types shared by every layer."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class Vector3:
    """A 3D vector: a position in meters or a velocity in meters per second.

    World frame (ADR-0008): +x is forward at takeoff, +y is left, +z is up.
    """

    ZERO: ClassVar["Vector3"]  # (0, 0, 0), like UE's FVector::ZeroVector; set below

    x: float
    y: float
    z: float

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scale: float) -> "Vector3":
        return Vector3(self.x * scale, self.y * scale, self.z * scale)


Vector3.ZERO = Vector3(0.0, 0.0, 0.0)
