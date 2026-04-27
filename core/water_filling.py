"""
Water filling simulation.
Simulates how resonance frequencies change as water fills a cavity.
Water level rises inversely proportional to cross-sectional area at constant flow rate.
"""
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .geometry import CavityGeometry, create_cylinder
from .solver_1d import TransferMatrixSolver1D, TMM1DResult
from .materials import Air


@dataclass
class WaterFillingResult:
    """Results from water filling simulation."""
    water_heights: np.ndarray            # Water height at each step (m)
    air_column_heights: np.ndarray       # Remaining air column height (m)
    time_values: np.ndarray              # Time at each step (s)
    resonance_tracking: List[List[float]]  # Resonance frequencies at each step
    full_results: List[TMM1DResult]       # Full TMM result at each step
    flow_rate: float                      # Volumetric flow rate (m³/s)


class WaterFillingSim:
    """
    Simulates water filling a cavity and tracks resonance changes.
    
    Physics:
        - Water surface acts as a rigid boundary (acoustic hard surface)
        - Air column above the water surface is the resonating cavity
        - Flow rate Q is constant
        - Rise rate: dh/dt = Q / A(h), where A(h) is cross-sectional area at height h
    """
    
    def __init__(self, medium: Optional[Air] = None):
        self.medium = medium or Air(temperature_celsius=20.0)
        self.solver = TransferMatrixSolver1D(self.medium)
    
    def simulate(self, geometry: CavityGeometry,
                 flow_rate: float = 1e-6,  # m³/s (= 1 mL/s)
                 num_steps: int = 50,
                 fill_fraction: float = 0.9,
                 freq_min: float = 100.0,
                 freq_max: float = 5000.0,
                 freq_points: int = 2000,
                 ):
        """
        Run water filling simulation. Yields progress updates.
        
        Args:
            geometry: Cavity geometry (full, empty shape)
            flow_rate: Volumetric flow rate in m³/s
            num_steps: Number of water level steps
            fill_fraction: Fill up to this fraction of total height (0 to 1)
            freq_min, freq_max: Frequency range for resonance search
            freq_points: Number of frequency points
        
        Yields:
            Tuple[int, float, List[float]]: (step_index, water_height, resonance_frequencies)
            The last yielded item is a tuple ("FINISH", WaterFillingResult)
        """
        max_water_height = geometry.height * fill_fraction
        
        # Calculate water heights considering variable cross-section
        # dh/dt = Q / A(h) → Δh_i = Q·Δt / A(h_i)
        # We choose steps so total time is distributed evenly
        water_heights, time_values = self._compute_water_heights(
            geometry, flow_rate, max_water_height, num_steps
        )
        
        air_column_heights = geometry.height - water_heights
        resonance_tracking = []
        full_results = []
        
        for i, wh in enumerate(water_heights):
            # Create air column geometry (from water surface to top)
            air_height = geometry.height - wh
            
            if air_height < 1e-4:  # Too little air left
                resonance_tracking.append([])
                full_results.append(None)
                yield i, wh, []
                continue
            
            # Create a new geometry representing only the air column above water
            air_geometry = self._extract_air_column(geometry, wh)
            
            # Solve: bottom = rigid (water surface), top = radiation (opening)
            result = self.solver.solve(
                air_geometry,
                freq_min=freq_min,
                freq_max=freq_max,
                freq_points=freq_points,
            )
            
            resonance_tracking.append(result.resonance_frequencies)
            full_results.append(result)
            
            # Yield progress: (current_step, current_height, current_resonances)
            yield i, wh, result.resonance_frequencies
        
        # Return final object through a custom yield if needed, 
        # but in Streamlit we'll just collect them in a list.
        yield "FINISH", WaterFillingResult(
            water_heights=water_heights,
            air_column_heights=air_column_heights,
            time_values=time_values,
            resonance_tracking=resonance_tracking,
            full_results=full_results,
            flow_rate=flow_rate,
        )
    
    def _compute_water_heights(self, geometry: CavityGeometry,
                                flow_rate: float,
                                max_height: float,
                                num_steps: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute water heights over time, accounting for variable cross-section.
        dh/dt = Q / A(h)
        
        Uses forward Euler integration with fine time steps, then
        samples at num_steps evenly spaced time points.
        """
        # Fine integration
        fine_steps = num_steps * 100
        h = 0.0
        heights = [0.0]
        times = [0.0]
        t = 0.0
        
        # Estimate total fill time
        # dt = dh * A(h) / Q
        dh_fine = max_height / fine_steps
        
        for _ in range(fine_steps):
            area = geometry.area_at(h)
            dt = dh_fine * area / flow_rate
            t += dt
            h += dh_fine
            if h > max_height:
                h = max_height
                heights.append(h)
                times.append(t)
                break
            heights.append(h)
            times.append(t)
        
        heights = np.array(heights)
        times = np.array(times)
        
        # Sample at evenly spaced time points
        t_samples = np.linspace(0, times[-1], num_steps)
        h_samples = np.interp(t_samples, times, heights)
        
        return h_samples, t_samples
    
    def _extract_air_column(self, geometry: CavityGeometry,
                             water_height: float) -> CavityGeometry:
        """
        Extract the air column geometry above the water surface.
        
        The air column goes from z=water_height to z=geometry.height in the
        original geometry. We create a new geometry where z=0 is the water
        surface and z=air_height is the opening.
        """
        air_height = geometry.height - water_height
        
        def air_radius_func(z):
            # z=0 in air column = water_height in original geometry
            return geometry.radius_at(water_height + z)
        
        return CavityGeometry(
            name=f"Air column (water at {water_height*100:.1f} cm)",
            height=air_height,
            radius_func=air_radius_func,
            num_segments=max(20, geometry.num_segments // 2),
        )
