"""
1D Transfer Matrix Method (TMM) solver for acoustic resonance in tubes.

Handles tubes with varying cross-section (frustum, bottle shapes) by dividing
into segments with piecewise-constant cross-sections and multiplying transfer matrices.

Convention:
    - z=0 is the BOTTOM (closed/rigid end)
    - z=L is the TOP (open end, radiation BC)
    - Segment transfer matrix relates left and right sides:
      [p_L]   [cos(kl)        j·Zc·sin(kl)] [p_R]
      [U_L] = [j/Zc·sin(kl)   cos(kl)      ] [U_R]
    - Total matrix: [p_0, U_0]^T = T_total · [p_N, U_N]^T
    
    For closed-open pipe:
      - z=0 rigid: U_0 = 0
      - z=L open: radiation impedance Z_rad applied
      - Input impedance at top: Z_in = p_N/U_N = -T22/T21
      - Resonances occur where |Z_in| is MINIMUM (admittance maximum)
"""
import numpy as np
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass

from .geometry import CavityGeometry
from .materials import Air
from .boundary import BoundaryCondition, BoundaryType


@dataclass
class TMM1DResult:
    """Results from 1D TMM simulation."""
    frequencies: np.ndarray          # Frequency array (Hz)
    impedance: np.ndarray            # Input impedance at the top (complex)
    transfer_function: np.ndarray    # Pressure transfer function magnitude
    resonance_frequencies: List[float]  # Detected resonance frequencies (Hz)
    mode_shapes: Optional[Dict[float, Tuple[np.ndarray, np.ndarray]]] = None


class TransferMatrixSolver1D:
    """
    1D Transfer Matrix Method solver for air column resonance.
    """
    
    def __init__(self, medium: Optional[Air] = None):
        self.medium = medium or Air(temperature_celsius=20.0)
    
    def _segment_transfer_matrix(self, length: float, area: float, 
                                  k: float, rho: float, c: float) -> np.ndarray:
        """
        Transfer matrix for a single cylindrical segment.
        [p_L, U_L]^T = T · [p_R, U_R]^T
        """
        Zc = rho * c / area  # Characteristic acoustic impedance
        cos_kl = np.cos(k * length)
        sin_kl = np.sin(k * length)
        
        return np.array([
            [cos_kl,            1j * Zc * sin_kl],
            [1j * sin_kl / Zc,  cos_kl          ]
        ], dtype=complex)
    
    def _radiation_impedance_unflanged(self, radius: float, k: float, 
                                        rho: float, c: float) -> complex:
        """
        Radiation impedance at an unflanged circular opening.
        Z_rad = (ρc/S) · [(ka)²/4 + j·0.6133·ka]
        """
        a = radius
        S = np.pi * a**2
        ka = k * a
        return (rho * c / S) * (0.25 * ka**2 + 1j * 0.6133 * ka)
    
    def _build_transfer_matrix(self, geometry: CavityGeometry, 
                               k: float | np.ndarray, rho: float, c: float,
                               ) -> np.ndarray:
        """
        Build total transfer matrix for the cavity.
        Supports both scalar k and vectorized np.ndarray k (F,).
        
        Returns:
            - If k is scalar: np.ndarray matrix (2, 2)
            - If k is array:  np.ndarray matrices (F, 2, 2)
        """
        n_seg = geometry.num_segments
        seg_length = geometry.height / n_seg
        z_vals, _ = geometry.get_profile(n_seg)
        
        z_mid = 0.5 * (z_vals[:-1] + z_vals[1:])
        a_mid = np.array([geometry.area_at(zm) for zm in z_mid])
        
        is_scalar = np.isscalar(k)
        k_vec = np.atleast_1d(k)
        F = len(k_vec)
        
        # Initialize T_total as identity matrices (F, 2, 2)
        T_total = np.zeros((F, 2, 2), dtype=complex)
        T_total[:, 0, 0] = 1.0
        T_total[:, 1, 1] = 1.0
        
        for seg in range(n_seg):
            Zc = rho * c / a_mid[seg]
            kl = k_vec * seg_length
            cos_kl = np.cos(kl)
            j_sin_kl = 1j * np.sin(kl)
            
            # Manual matmul for T_total = T_total @ T_seg
            t11, t12 = T_total[:, 0, 0], T_total[:, 0, 1]
            t21, t22 = T_total[:, 1, 0], T_total[:, 1, 1]
            
            j_sin_Zc = j_sin_kl / Zc
            Zc_j_sin = Zc * j_sin_kl
            
            T_total[:, 0, 0] = t11 * cos_kl + t12 * j_sin_Zc
            T_total[:, 0, 1] = t11 * Zc_j_sin + t12 * cos_kl
            T_total[:, 1, 0] = t21 * cos_kl + t22 * j_sin_Zc
            T_total[:, 1, 1] = t21 * Zc_j_sin + t22 * cos_kl
            
        return T_total[0] if is_scalar else T_total

    def solve(self, geometry: CavityGeometry,
              freq_min: float = 20.0, freq_max: float = 5000.0, 
              freq_points: int = 2000,
              ) -> TMM1DResult:
        """
        Solve for acoustic response of a closed-open cavity using vectorized TMM.
        """
        rho = self.medium.density
        c = self.medium.speed_of_sound
        
        frequencies = np.linspace(freq_min, freq_max, freq_points)
        valid_f = frequencies.copy()
        valid_f[valid_f < 1e-3] = 1e-3
        k = 2.0 * np.pi * valid_f / c
        
        # Build vectorized matrices (F, 2, 2)
        T = self._build_transfer_matrix(geometry, k, rho, c)
        T11, T12, T21, T22 = T[:, 0, 0], T[:, 0, 1], T[:, 1, 0], T[:, 1, 1]
        
        # Radiation impedance at opening (vectorized)
        r_top = geometry.radius_at(geometry.height)
        Z_rad = self._radiation_impedance_unflanged(r_top, k, rho, c)
        
        # Tube input impedance (vectorized)
        # Z_in_tube = T22 / T21
        input_impedance = np.zeros_like(frequencies, dtype=complex)
        mask_t21 = np.abs(T21) > 1e-30
        input_impedance[mask_t21] = T22[mask_t21] / T21[mask_t21]
        input_impedance[~mask_t21] = 1e30 + 0j
        
        # Total input impedance
        input_impedance = input_impedance + Z_rad
        
        # Transfer function H = p_0 / p_source = 1.0 / (T22 + T21 * Z_rad)
        Z_total = T22 + T21 * Z_rad
        transfer_func = np.zeros_like(frequencies, dtype=float)
        mask_ztot = np.abs(Z_total) > 1e-30
        transfer_func[mask_ztot] = np.abs(1.0 / Z_total[mask_ztot])
        
        # Find resonances
        resonances = self._find_resonances(frequencies, transfer_func, prominence=0.1)
        
        # Compute mode shapes (including end correction for visualization)
        r_top = geometry.radius_at(geometry.height)
        delta = 0.6133 * r_top
        
        mode_shapes = {}
        for f_res in resonances:
            z_mode, p_mode = self._compute_mode_shape(geometry, f_res, end_correction=delta)
            mode_shapes[f_res] = (z_mode, p_mode)
        
        return TMM1DResult(
            frequencies=frequencies,
            impedance=input_impedance,
            transfer_function=transfer_func,
            resonance_frequencies=resonances,
            mode_shapes=mode_shapes,
        )
    
    def _find_resonances(self, frequencies: np.ndarray, 
                          response: np.ndarray,
                          prominence: float = 0.5) -> List[float]:
        """Find resonance frequencies from peaks in response (admittance)."""
        from scipy.signal import find_peaks
        
        log_resp = np.log10(response + 1e-30)
        
        peaks, _ = find_peaks(log_resp, prominence=prominence, distance=10)
        
        # Refine peak positions using parabolic interpolation
        df = frequencies[1] - frequencies[0] if len(frequencies) > 1 else 1.0
        refined_freqs = []
        for p in peaks:
            if 1 <= p <= len(frequencies) - 2:
                y0, y1, y2 = log_resp[p-1], log_resp[p], log_resp[p+1]
                denom = 2.0 * (2.0 * y1 - y0 - y2)
                if abs(denom) > 1e-30:
                    delta_f = (y0 - y2) / denom
                    refined_freqs.append(float(frequencies[p] + delta_f * df))
                else:
                    refined_freqs.append(float(frequencies[p]))
            else:
                refined_freqs.append(float(frequencies[p]))
        
        return refined_freqs
    
    def _compute_mode_shape(self, geometry: CavityGeometry, 
                             frequency: float,
                             end_correction: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
        """Compute pressure distribution along the tube at a given frequency."""
        rho = self.medium.density
        c = self.medium.speed_of_sound
        k = 2.0 * np.pi * frequency / c
        
        n_seg = geometry.num_segments
        z_vals, _ = geometry.get_profile(n_seg)
        seg_length = geometry.height / n_seg
        z_mid = 0.5 * (z_vals[:-1] + z_vals[1:])
        a_mid = np.array([geometry.area_at(zm) for zm in z_mid])
        
        # Get Z_in to determine p_N/U_N ratio
        T_total = self._build_transfer_matrix(geometry, k, rho, c)
        T21, T22 = T_total[1, 0], T_total[1, 1]
        
        # Set U_N = 1 (arbitrary), p_N = Z_in = -T22/T21
        U_N = 1.0 + 0j
        p_N = -T22 / T21 if abs(T21) > 1e-30 else 1.0 + 0j
        
        # Propagate from top to bottom
        z_points = [z_vals[n_seg]]
        p_points = [np.abs(p_N)]
        
        state = np.array([p_N, U_N], dtype=complex)
        for seg in range(n_seg - 1, -1, -1):
            T_seg = self._segment_transfer_matrix(seg_length, a_mid[seg], k, rho, c)
            state = T_seg @ state
            z_points.append(z_vals[seg])
            p_points.append(np.abs(state[0]))
        
        z_out = np.array(z_points[::-1])
        p_out = np.array(p_points[::-1])
        
        # Add end correction tail (virtual extension where p goes to 0)
        if end_correction > 0:
            # We assume a sinusoidal continuation: p(z) = PN * cos(k_eff * (z - L))
            # But simpler for visualization: p(L+delta) = 0
            n_extra = 20
            z_extra = np.linspace(geometry.height, geometry.height + end_correction, n_extra + 1)[1:]
            p_at_L = p_out[-1]
            # Linearly drop to 0 for visualization since TMM assumes radiation impedance
            p_extra = p_at_L * (1 - (z_extra - geometry.height) / end_correction)
            
            z_out = np.concatenate([z_out, z_extra])
            p_out = np.concatenate([p_out, p_extra])
        
        p_max = np.max(p_out)
        if p_max > 0:
            p_out = p_out / p_max
        
        return z_out, p_out

    def solve_frustum_theory(self, L: float, r1: float, r2: float) -> List[float]:
        """
        Solve the transcendental equation for a conical frustum:
        tan(kL) = -kx1  where x1 is distance from small end to vertex.
        """
        from scipy.optimize import fsolve
        
        c = self.medium.speed_of_sound
        # x1: vertex distance from smaller end (r1)
        if abs(r2 - r1) < 1e-6:
            # Degenerate case: Cylinder
            return [(2*n - 1) * c / (4 * L) for n in range(1, 5)]
        
        # vertex is always relative to smaller end
        r_min, r_max = min(r1, r2), max(r1, r2)
        x1 = r_min * L / (r_max - r_min)
        
        def equation(k):
            # Using tan(kL) + kx1 = 0
            # To avoid discontinuities in tan, use sin(kL) + kx1 cos(kL) = 0
            return np.sin(k * L) + k * x1 * np.cos(k * L)
        
        # Solve for first few modes
        results_f = []
        for n in range(1, 5):
            # Initial guess: somewhere between (n-1/2)pi/L and n*pi/L
            # For cylinder it's (n-0.5)*pi/L. For cone it's n*pi/L.
            guess_k = (n - 0.25) * np.pi / L
            k_sol = fsolve(equation, guess_k)[0]
            if k_sol > 0:
                results_f.append(float(k_sol * c / (2 * np.pi)))
        
        return sorted(list(set(np.round(results_f, 1))))
