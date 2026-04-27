import pandas as pd
import numpy as np
import os

def test_csv_cycle():
    # 1. Simulate app.py export logic
    num_steps = 30
    time_values = np.linspace(0, 5, num_steps)
    water_heights = np.linspace(0, 0.1, num_steps)
    resonance_tracking = [[100 + i, 300 + i] for i in range(num_steps)]
    flow_rate_ml = 5.0
    
    # Block 1
    ts_data = {
        'time_s': time_values,
        'water_height_cm': water_heights * 100,
    }
    for m in range(2):
        ts_data[f'f_mode{m+1}_Hz'] = [f[m] for f in resonance_tracking]
    df_ts = pd.DataFrame(ts_data)
    df_ts['|'] = '|'
    
    # Block 2
    n_profile = 100
    z_prof = np.linspace(0, 0.15, n_profile)
    r_prof = np.linspace(0.03, 0.05, n_profile)
    static_data = {
        'flow_rate_mLs': [flow_rate_ml] + [np.nan] * (n_profile - 1),
        'profile_z_m': z_prof,
        'profile_r_m': r_prof,
    }
    df_static = pd.DataFrame(static_data)
    
    df_export = pd.concat([df_ts, df_static], axis=1)
    df_export.to_csv('test_format.csv', index=False)
    print("CSV created successfully.")

    # 2. Simulate inverse_app.py load logic
    df = pd.read_csv('test_format.csv')
    
    def find_column(df, patterns):
        cols_lower = {c.lower().strip(): c for c in df.columns}
        for pat in patterns:
            if pat.lower() in cols_lower:
                return cols_lower[pat.lower()]
        return None

    time_col = find_column(df, ['time_s'])
    gt_z_col = find_column(df, ['profile_z_m'])
    gt_r_col = find_column(df, ['profile_r_m'])
    flow_col = find_column(df, ['flow_rate_mLs'])
    
    t_data = df[time_col].dropna().values
    gt_z = df[gt_z_col].dropna().values
    gt_r = df[gt_r_col].dropna().values
    flow_val = df[flow_col].iloc[0]
    
    print(f"Time data length: {len(t_data)} (Expected: 30)")
    print(f"Profile Z length: {len(gt_z)} (Expected: 100)")
    print(f"Profile R length: {len(gt_r)} (Expected: 100)")
    print(f"Flow rate: {flow_val} (Expected: 5.0)")
    
    assert len(t_data) == 30
    assert len(gt_z) == 100
    assert len(gt_r) == 100
    assert flow_val == 5.0
    print("Verification PASSED!")

if __name__ == "__main__":
    test_csv_cycle()
