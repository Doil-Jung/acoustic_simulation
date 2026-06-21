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
                 air_num_segments: int = 30,
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
        # v2: fill_fraction은 부피 기준 (generate_spectrum_dataset.py와 동일)
        # 높이의 90%가 아니라, 전체 부피의 90%에 해당하는 수위까지 채움
        water_heights, time_values = self._compute_water_heights(
            geometry, flow_rate, fill_fraction, num_steps
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
            air_geometry = self._extract_air_column(geometry, wh, air_num_segments)
            
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
                                fill_fraction: float,
                                num_steps: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute water heights over time, accounting for variable cross-section.
        
        v2: 부피 등분 방식 (generate_spectrum_dataset.py와 동일)
        - 전체 높이까지의 누적 부피 V(z)를 계산
        - fill_fraction은 부피 기준 (0.9 = 전체 부피의 90%)
        - 목표 부피를 num_steps 등분하여 각 부피에 해당하는 수위를 역산
        """
        # 전체 높이까지의 누적 부피 프로파일 V(z) 계산
        n_fine = 200
        z_eval = np.linspace(0, geometry.height, n_fine)
        areas = np.array([geometry.area_at(z) for z in z_eval])
        dz = geometry.height / (n_fine - 1)
        V_cum = np.cumsum(areas * dz)
        V_cum = np.insert(V_cum, 0, 0.0)[:-1]  # V(0) = 0
        total_vol = V_cum[-1]
        
        # fill_fraction을 부피 기준으로 적용
        target_vol_max = total_vol * fill_fraction
        
        # 부피를 num_steps 등분하여 수위 계산
        volumes_sample = np.linspace(0, target_vol_max, num_steps)
        h_samples = np.interp(volumes_sample, V_cum, z_eval)
        
        # 시간 계산: t = V / Q
        t_samples = volumes_sample / flow_rate
        
        return h_samples, t_samples
    
    def _extract_air_column(self, geometry: CavityGeometry,
                             water_height: float,
                             air_num_segments: int = 30) -> CavityGeometry:
        """
        Extract the air column geometry above the water surface.
        
        The air column goes from z=water_height to z=geometry.height in the
        original geometry. We create a new geometry where z=0 is the water
        surface and z=air_height is the opening.
        
        Args:
            air_num_segments: TMM 세그먼트 수. 학습 데이터와 동일한 값(30)을
                사용해야 학습-추론 간 스펙트럼이 일치합니다.
        """
        air_height = geometry.height - water_height
        
        def air_radius_func(z):
            # z=0 in air column = water_height in original geometry
            return geometry.radius_at(water_height + z)
        
        return CavityGeometry(
            name=f"Air column (water at {water_height*100:.1f} cm)",
            height=air_height,
            radius_func=air_radius_func,
            num_segments=air_num_segments,
        )
