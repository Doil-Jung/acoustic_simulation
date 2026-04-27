import numpy as np
import pandas as pd
import os
from core.geometry import CavityGeometry
from core.water_filling import WaterFillingSim
from core.materials import Air

def make_cone_csv():
    # Parameters for Truncated Cone
    H = 0.20 # 20cm height
    r_base = 0.06 # 6cm at bottom (z=0)
    r_top = 0.02 # 2cm at top (z=0.20)
    
    def r_func(z):
        return r_base + (r_top - r_base) * (z / H)
        
    geo = CavityGeometry(
        name="TruncatedCone",
        height=H,
        radius_func=r_func,
        num_segments=100
    )
    
    medium = Air()
    sim = WaterFillingSim(medium)
    Q = 5e-6 # 5mL/s
    NUM_STEPS = 30
    
    print("Simulating Truncated Cone (Base: 6cm, Top: 2cm)...")
    gen = sim.simulate(geo, flow_rate=Q, num_steps=NUM_STEPS, fill_fraction=0.95, freq_max=4000, freq_points=1000)
    final_result = None
    for update in gen:
        if isinstance(update, tuple) and update[0] == "FINISH":
            final_result = update[1]
            break
            
    if final_result is None:
        print("Simulation failed.")
        return
        
    # Extract features for X (Input)
    max_modes = 3
    times = final_result.time_values
    f_traj = np.zeros((len(times), max_modes))
    
    for step_idx, freqs in enumerate(final_result.resonance_tracking):
        for m in range(max_modes):
            if m < len(freqs):
                f_traj[step_idx, m] = freqs[m]
            else:
                f_traj[step_idx, m] = np.nan
                
    # Ground truth for Y (Label)
    # WaterFillingSim creates linearly spaced heights
    max_fill_height = H * 0.95
    water_heights = np.linspace(0, max_fill_height, len(times))
    target_radius = [r_func(z) for z in water_heights]
    
    df = pd.DataFrame({
        'time_s': times,
        'f_mode1_Hz': f_traj[:, 0],
        'f_mode2_Hz': f_traj[:, 1],
        'f_mode3_Hz': f_traj[:, 2],
        'target_radius_m': target_radius,
        'ground_truth_z_m': water_heights
    })
    
    out_dir = 'dataset'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    out_path = os.path.join(out_dir, 'truncated_cone.csv')
    df.to_csv(out_path, index=False)
    print(f"Saved truncated cone dataset to '{out_path}'")

if __name__ == "__main__":
    make_cone_csv()
