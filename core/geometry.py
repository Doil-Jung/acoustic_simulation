"""
Geometry definitions for acoustic simulation.
Defines cross-sectional profiles for axisymmetric cavities (cups, bottles).
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable


@dataclass
class CavityGeometry:
    """
    Axisymmetric cavity defined by its radius profile r(z).
    z=0 is the bottom (closed end), z=height is the opening.
    """
    name: str
    height: float  # Total height in meters
    radius_func: Callable[[float], float]  # r(z) function
    num_segments: int = 100  # Number of segments for discretization
    
    def radius_at(self, z: float) -> float:
        """Get radius at height z."""
        return self.radius_func(z)
    
    def area_at(self, z: float) -> float:
        """Get cross-sectional area at height z."""
        r = self.radius_at(z)
        return np.pi * r ** 2
    
    def get_profile(self, n: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get discretized profile (z_array, r_array).
        
        Returns:
            Tuple of (z_values, radius_values)
        """
        n = n or self.num_segments
        z = np.linspace(0, self.height, n + 1)
        r = np.array([self.radius_func(zi) for zi in z])
        return z, r
    
    def get_areas(self, n: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get discretized areas (z_array, area_array).
        
        Returns:
            Tuple of (z_values, area_values)
        """
        z, r = self.get_profile(n)
        return z, np.pi * r ** 2
    
    def volume(self) -> float:
        """Calculate total volume using numerical integration."""
        z, areas = self.get_areas(1000)
        return np.trapezoid(areas, z)


def create_cylinder(height: float, radius: float, name: str = "Cylinder") -> CavityGeometry:
    """
    Create a cylindrical cavity.
    
    Args:
        height: Height in meters
        radius: Radius in meters
    """
    return CavityGeometry(
        name=name,
        height=height,
        radius_func=lambda z: radius,
        num_segments=100,
    )


def create_frustum(height: float, r_bottom: float, r_top: float, 
                   name: str = "Frustum") -> CavityGeometry:
    """
    Create a frustum (truncated cone) cavity.
    
    Args:
        height: Height in meters
        r_bottom: Bottom radius in meters (z=0, closed end)
        r_top: Top radius in meters (z=height, open end)
    """
    def radius_func(z):
        t = z / height if height > 0 else 0
        return r_bottom + (r_top - r_bottom) * t
    
    return CavityGeometry(
        name=name,
        height=height,
        radius_func=radius_func,
        num_segments=100,
    )


def create_bottle(height: float, body_radius: float, neck_radius: float,
                  neck_height: float, name: str = "Bottle") -> CavityGeometry:
    """
    Create a bottle-shaped cavity with a body and narrow neck.
    Uses smooth cosine transition between body and neck.
    
    Args:
        height: Total height in meters
        body_radius: Body (wide part) radius
        neck_radius: Neck (narrow part) radius  
        neck_height: Height where neck starts (from bottom)
    """
    transition_width = (height - neck_height) * 0.3  # 30% of neck region for transition
    
    def radius_func(z):
        if z <= neck_height - transition_width:
            return body_radius
        elif z <= neck_height + transition_width:
            # Smooth cosine transition
            t = (z - (neck_height - transition_width)) / (2 * transition_width)
            return body_radius + (neck_radius - body_radius) * 0.5 * (1 - np.cos(np.pi * t))
        else:
            return neck_radius
    
    return CavityGeometry(
        name=name,
        height=height,
        radius_func=radius_func,
        num_segments=200,
    )


def create_custom(height: float, z_points: List[float], r_points: List[float],
                  name: str = "Custom") -> CavityGeometry:
    """
    Create a cavity from custom radius profile points.
    Uses linear interpolation between points.
    
    Args:
        height: Total height in meters
        z_points: Height values (must be sorted, 0 to height)
        r_points: Corresponding radius values
    """
    from scipy.interpolate import interp1d
    interp = interp1d(z_points, r_points, kind='linear', fill_value='extrapolate')
    
    return CavityGeometry(
        name=name,
        height=height,
        radius_func=lambda z: float(interp(z)),
        num_segments=100,
    )
