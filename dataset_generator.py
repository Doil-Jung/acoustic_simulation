"""
Machine Learning Dataset Generator for Inverse Acoustic Problem

Generates random cavity geometries and runs water-filling simulations
to build a dataset mapping [Time-Frequency Trajectories] to [Radius Profiles].
"""

import numpy as np
import pandas as pd
import os
import time
from scipy.interpolate import CubicSpline
from typing import Tuple, List

# Core modules
from core.geometry import CavityGeometry
from core.water_filling import WaterFillingSim
from core.materials import Air


def generate_random_spline_profile(height: float, num_knots: int = 5,
                                   min_radius: float = 0.01,
                                   max_radius: float = 0.1) -> CavityGeometry:
    """
    Creates a random cavity shape using a smooth cubic spline.
    """
    z_knots = np.linspace(0, height, num_knots)
    r_knots = np.random.uniform(min_radius, max_radius, num_knots)
    
    # Ensure minimum neck or base constraints if desired
    # For now, totally random smooth shape
    spline = CubicSpline(z_knots, r_knots)
    
    def r_func(z):
        # Clip to min/max to avoid negative or exaggerated radii
        val = spline(z)
        return float(np.clip(val, min_radius, max_radius))
        
    return CavityGeometry(
        name=f"RandomSpline_{np.random.randint(1000, 9999)}",
        height=height,
        radius_func=r_func,
        num_segments=100
    )


def batch_generate(num_samples: int, output_dir: str = "dataset"):
    """
    Run simulations for multiple random shapes and save the raw pairs.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    medium = Air()
    sim = WaterFillingSim(medium)
    
    # Configuration
    H_L = 0.20        # Fixed height (20 cm)
    Q = 5e-6          # 5 mL/s (Constant Flow Rate)
    NUM_STEPS = 20    # Resolution of time-series
    
    print(f"Starting generation of {num_samples} samples...")
    t0 = time.time()
    
    # NPZ Archives
    all_radii = []          # Y label: Radii profile array
    all_trajectories = []   # X input: Frequency trajectories (NUM_STEPS, n_modes)
    all_times = []          # X input: Time vector
    target_z = np.linspace(0, H_L, NUM_STEPS) # Z-points for evaluating Y (Ground Truth Radii)
    
    for i in range(num_samples):
        # Vary flow rate slightly for data augmentation (Optional, keep fixed for now)
        current_Q = Q 
        
        geo = generate_random_spline_profile(H_L, num_knots=np.random.randint(4, 8))
        
        # Ground Truth Y shape
        r_profile = np.array([geo.radius_at(z) for z in target_z])
        
        # Forward Simulation
        try:
            gen = sim.simulate(geo, flow_rate=current_Q, num_steps=NUM_STEPS, fill_fraction=0.95, freq_max=4000, freq_points=500)
            final_result = None
            for update in gen:
                if isinstance(update, tuple) and update[0] == "FINISH":
                    final_result = update[1]
                    break
                    
            if final_result is None:
                continue
                
        except Exception as e:
            print(f"[Warning] Simulation failed for sample {i}: {e}")
            continue
            
        # Extract features (X)
        max_modes = 3
        f_traj = np.zeros((len(final_result.time_values), max_modes))
        
        for step_idx, freqs in enumerate(final_result.resonance_tracking):
            # Pad or truncate to max_modes
            for m in range(max_modes):
                if m < len(freqs):
                    f_traj[step_idx, m] = freqs[m]
                else:
                    f_traj[step_idx, m] = np.nan
        
        # Check alignment (sometimes simulator steps and time_values differ slightly)
        if len(final_result.time_values) != len(target_z):
             # Interpolate to match NUM_STEPS if needed, but WaterFillingSim typically returns matched sizes
             pass
             
        all_radii.append(r_profile)
        all_trajectories.append(f_traj)
        all_times.append(final_result.time_values)
        
        if (i+1) % 10 == 0:
            print(f"[{i+1}/{num_samples}] Processed. Elapsed: {time.time()-t0:.1f}s")
    
    # Save as NPZ archive
    np.savez(os.path.join(output_dir, "acoustic_inverse_dataset.npz"),
             radii=np.array(all_radii),                # Y (Ground Truth)
             trajectories=np.array(all_trajectories), # X: Frequencies
             times=np.array(all_times),               # X: Time axis
             z_points=target_z,                       # Domain of Y
             flow_rate=np.array([Q]*len(all_radii)))  # Q constants
             
    print(f"Saved dataset of shape {np.array(all_trajectories).shape} to '{output_dir}'.")


if __name__ == "__main__":
    # Test run generating 5 samples
    batch_generate(num_samples=5)
