"""
Boundary conditions for acoustic simulation.
"""
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class BoundaryType(Enum):
    """Types of acoustic boundary conditions."""
    RIGID = "rigid"           # Hard wall: ∂p/∂n = 0
    PRESSURE_SOURCE = "pressure_source"  # Fixed pressure: p = p₀
    VELOCITY_SOURCE = "velocity_source"  # Vibrating surface: ∂p/∂n = -jωρv₀
    RADIATION = "radiation"   # Open end / absorbing: ∂p/∂n = -jkp


@dataclass
class BoundaryCondition:
    """
    Acoustic boundary condition specification.
    """
    bc_type: BoundaryType
    amplitude: float = 1.0  # Source amplitude (Pa for pressure, m/s for velocity)
    phase: float = 0.0      # Source phase in radians
    
    @property
    def is_source(self) -> bool:
        return self.bc_type in (BoundaryType.PRESSURE_SOURCE, BoundaryType.VELOCITY_SOURCE)
    
    @property
    def is_natural(self) -> bool:
        """Naturally satisfied in FEM (no explicit assembly needed)."""
        return self.bc_type == BoundaryType.RIGID


def rigid_wall() -> BoundaryCondition:
    """Create a rigid wall boundary (perfect reflection)."""
    return BoundaryCondition(bc_type=BoundaryType.RIGID)


def pressure_source(amplitude: float = 1.0, phase: float = 0.0) -> BoundaryCondition:
    """Create a pressure source boundary."""
    return BoundaryCondition(
        bc_type=BoundaryType.PRESSURE_SOURCE,
        amplitude=amplitude,
        phase=phase,
    )


def velocity_source(amplitude: float = 1e-3, phase: float = 0.0) -> BoundaryCondition:
    """Create a velocity source (vibrating surface) boundary."""
    return BoundaryCondition(
        bc_type=BoundaryType.VELOCITY_SOURCE,
        amplitude=amplitude,
        phase=phase,
    )


def radiation() -> BoundaryCondition:
    """Create a radiation (open/absorbing) boundary."""
    return BoundaryCondition(bc_type=BoundaryType.RADIATION)
