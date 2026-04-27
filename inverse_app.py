"""
Inverse Acoustic Shape Estimator v3.0

Reconstructs cup geometry from resonance frequency trajectories during water filling.
Uses Differential Evolution (global) + L-BFGS-B (local) two-stage optimization.
Reuses the same TMM forward solver as the main app for physics consistency.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from scipy.optimize import differential_evolution, minimize
from scipy.signal import savgol_filter
import time
import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.geometry import CavityGeometry
from core.materials import Air
from core.solver_1d import TransferMatrixSolver1D

# Matplotlib Korean Font Support
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ═══════════════════════════════════════════════════════════
# Page Config
# ═══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Inverse Shape Estimator v3.0",
    page_icon="🔬",
    layout="wide",
)

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #E65100; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1rem; color: #666; margin-bottom: 2rem; }
    .stProgress > div > div > div { background-color: #E65100; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🔬 Inverse Shape Estimator v3.0</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">물 채움 공명 데이터로부터 컵 형상을 역추정합니다 — DE 전역 탐색 + L-BFGS-B 정밀 최적화</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# Session State
# ═══════════════════════════════════════════════════════════
for key, default in [
    ('opt_running', False),
    ('opt_finished', False),
    ('opt_result', None),
    ('best_x', None),
    ('history', []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ═══════════════════════════════════════════════════════════
# Column Detection Utilities
# ═══════════════════════════════════════════════════════════
def find_column(df, patterns, required=False):
    """Find a column by trying multiple name patterns (case-insensitive)."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for pat in patterns:
        if pat.lower() in cols_lower:
            return cols_lower[pat.lower()]
    if required:
        st.error(f"필수 컬럼을 찾을 수 없습니다: {patterns}")
        st.stop()
    return None

def load_frequency_columns(df):
    """Load all available f_modeN_Hz columns."""
    mode_cols = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl.startswith('f_mode') and cl.endswith('_hz'):
            try:
                mode_num = int(cl.replace('f_mode', '').replace('_hz', ''))
                mode_cols[mode_num] = col
            except ValueError:
                continue
    return mode_cols

# ═══════════════════════════════════════════════════════════
# Forward Simulation Engine (reuses core TMM)
# ═══════════════════════════════════════════════════════════
def build_geometry_from_params(H, radii_ctrl, n_ctrl):
    """Build CavityGeometry from spline control points."""
    radii_ctrl = np.clip(radii_ctrl, 0.003, 0.20)
    H = np.clip(H, 0.01, 0.60)
    z_ctrl = np.linspace(0, H, n_ctrl)
    spline = CubicSpline(z_ctrl, radii_ctrl, bc_type='natural')
    
    def radius_func(z):
        r = float(spline(np.clip(z, 0, H)))
        return max(0.003, min(0.20, r))
    
    return CavityGeometry(
        name="Estimated",
        height=H,
        radius_func=radius_func,
        num_segments=60,
    )

def simulate_resonances_at_water_heights(geometry, water_heights_m, medium, 
                                          freq_min=50, freq_max=5000, freq_points=1500):
    """
    For each water height, compute the air column resonances using the exact same
    TMM solver as the forward simulation (core/solver_1d.py).
    """
    solver = TransferMatrixSolver1D(medium)
    all_resonances = []
    
    for wh in water_heights_m:
        air_height = geometry.height - wh
        
        if air_height < 1e-4:
            all_resonances.append([])
            continue
        
        # Create air column geometry (same as water_filling.py)
        def make_air_func(wh_val):
            def air_radius_func(z):
                return geometry.radius_at(wh_val + z)
            return air_radius_func
        
        air_geo = CavityGeometry(
            name="air_column",
            height=air_height,
            radius_func=make_air_func(wh),
            num_segments=max(20, 50),
        )
        
        try:
            result = solver.solve(air_geo, freq_min=freq_min, freq_max=freq_max,
                                  freq_points=freq_points)
            all_resonances.append(result.resonance_frequencies)
        except Exception:
            all_resonances.append([])
    
    return all_resonances

def compute_volume_profile(geometry, n_points=200):
    """Compute cumulative volume V(z) for the geometry."""
    z_eval = np.linspace(0, geometry.height, n_points)
    areas = np.array([geometry.area_at(z) for z in z_eval])
    dz = geometry.height / (n_points - 1)
    V_cum = np.cumsum(areas * dz)
    V_cum = np.insert(V_cum, 0, 0.0)[:-1]  # shift so V(0) = 0
    return z_eval, V_cum

def volumes_to_water_heights(geometry, volumes_m3, n_points=200):
    """Convert liquid volumes to water heights using geometry."""
    z_eval, V_cum = compute_volume_profile(geometry, n_points)
    # Clip volumes to valid range
    volumes_clipped = np.clip(volumes_m3, 0, V_cum[-1] - 1e-9)
    water_heights = np.interp(volumes_clipped, V_cum, z_eval)
    return water_heights

# ═══════════════════════════════════════════════════════════
# Harmonic/Formant Analysis
# ═══════════════════════════════════════════════════════════
def analyze_cavity_type(measured_freqs):
    """Analyze the ratio of resonance frequencies to infer cavity type."""
    if 1 not in measured_freqs or 2 not in measured_freqs:
        return "데이터 부족 (f1, f2 필요)"
    
    f1 = measured_freqs[1]
    f2 = measured_freqs[2]
    
    # Use the initial frequencies (no/little water) for type analysis
    valid = np.isfinite(f1) & np.isfinite(f2)
    if np.sum(valid) == 0:
        return "데이터 유효성 부족"
    
    # Calculate average ratio of f2/f1
    ratio = np.nanmean(f2[valid] / f1[valid])
    
    if ratio > 4.5:
        return f"호리병형/플라스크 (Helmholtz) [Ratio: {ratio:.2f}]"
    elif ratio > 3.2:
        return f"축소 원뿔대형 (Narrowing) [Ratio: {ratio:.2f}]"
    elif ratio < 2.2:
        return f"확대 원뿔대형 (Widening) [Ratio: {ratio:.2f}]"
    elif 2.8 < ratio < 3.2:
        return f"실린더형 [Ratio: {ratio:.2f}]"
    else:
        return f"일반 변칙 형상 [Ratio: {ratio:.2f}]"

# ═══════════════════════════════════════════════════════════
# Objective Function
# ═══════════════════════════════════════════════════════════
def create_objective(t_data, measured_freqs, flow_rate, medium,
                     n_ctrl, mode_weights, reg_weight, 
                     n_sample=12, freq_max=5000,
                     callback_fn=None, log_file=None):
    """
    Create the objective function for optimization.
    """
    # Subsample time points for efficiency
    indices = np.unique(np.linspace(0, len(t_data)-1, n_sample, dtype=int))
    t_sample = t_data[indices]
    V_sample = flow_rate * t_sample  # volumes at sampled times
    
    eval_count = [0]
    
    # Create directory for logs if needed
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    def objective(x):
        eval_count[0] += 1
        
        if not np.all(np.isfinite(x)):
            return 1e12
        
        H = x[0]
        radii_ctrl = x[1:n_ctrl+1]
        
        try:
            geometry = build_geometry_from_params(H, radii_ctrl, n_ctrl)
        except Exception:
            return 1e12
        
        # Convert volumes to water heights for this geometry
        try:
            wh_sample = volumes_to_water_heights(geometry, V_sample)
        except Exception:
            return 1e12
        
        # Simulate resonances - Use lower freq_points for speed during optimization
        sim_res = simulate_resonances_at_water_heights(
            geometry, wh_sample, medium,
            freq_min=50, freq_max=freq_max, freq_points=500
        )
        
        # Multi-mode error
        total_error = 0.0
        n_comparisons = 0
        sim_freqs_for_plot = {}
        
        for mode_num, weight in mode_weights.items():
            if weight <= 0 or mode_num not in measured_freqs:
                continue
            
            f_meas = measured_freqs[mode_num][indices]
            f_sim = []
            
            for i, res in enumerate(sim_res):
                if mode_num - 1 < len(res):
                    f_sim.append(res[mode_num - 1])
                else:
                    f_sim.append(np.nan)
            
            f_sim = np.array(f_sim)
            valid = np.isfinite(f_meas) & np.isfinite(f_sim)
            
            if np.sum(valid) > 0:
                # Relative error (scale-invariant)
                rel_err = (f_sim[valid] - f_meas[valid]) / f_meas[valid]
                rms = np.sqrt(np.mean(rel_err**2))
                total_error += weight * rms
                n_comparisons += 1
            
            sim_freqs_for_plot[mode_num] = f_sim
        
        if n_comparisons == 0:
            return 1e12
        
        # Smoothness regularization (penalize wiggly profiles)
        if len(radii_ctrl) >= 3:
            d2r = np.diff(radii_ctrl, 2)
            smooth_penalty = reg_weight * np.sum(d2r**2) * 1e4
        else:
            smooth_penalty = 0.0
        
        # Volume constraint: total volume should be consistent
        total_vol_geom = geometry.volume()
        total_vol_data = flow_rate * t_data[-1]
        # Allow some headroom since we don't fill to 100%
        vol_ratio = total_vol_geom / max(total_vol_data, 1e-10)
        if vol_ratio < 0.8:
            vol_penalty = (0.8 - vol_ratio)**2 * 10.0
        else:
            vol_penalty = 0.0
        
        cost = total_error + smooth_penalty + vol_penalty
        
        # Logging for Machine Learning
        if log_file:
            try:
                with open(log_file, 'a') as f:
                    # ML Dataset Row: H, r0...rN, f1_0...f1_M, f2_0...f2_M, cost
                    row = [H] + list(radii_ctrl)
                    
                    # Pad or clip frequencies to a fixed size (n_sample)
                    for mode in [1, 2]:
                        f_arr = sim_freqs_for_plot.get(mode, np.full(n_sample, np.nan))
                        
                        # Ensure f_arr is exactly length n_sample (pad if needed)
                        f_padded = np.full(n_sample, np.nan)
                        valid_len = min(n_sample, len(f_arr))
                        f_padded[:valid_len] = f_arr[:valid_len]
                        
                        row.extend(list(f_padded))
                        
                    row.append(cost)
                    
                    # Format strictly to 6 decimal places to keep CSV manageable
                    f.write(','.join([f"{val:.6f}" if np.isfinite(val) else "NaN" for val in row]) + '\n')
            except Exception:
                pass

        # Callback for visualization
        if callback_fn is not None and eval_count[0] % 5 == 0:
            callback_fn(x, cost, sim_freqs_for_plot, indices, eval_count[0])
        
        return cost if np.isfinite(cost) else 1e12
    
    return objective, indices

# ═══════════════════════════════════════════════════════════
# Physics-Informed Initialization
# ═══════════════════════════════════════════════════════════
def physics_init(f1_data, t_data, Q, c, n_ctrl):
    """
    Improved initialization using Differential Inversion:
    A(L) = (4*Q / c) / [d(1/f1)/dt]
    """
    valid = np.isfinite(f1_data) & np.isfinite(t_data)
    if np.sum(valid) < 5:
        return 0.15, np.full(n_ctrl, 0.04), 0.0
    
    t_v = t_data[valid]
    y_v = 1.0 / f1_data[valid]
    
    try:
        # 1. Cylinder Fit (Global Trend)
        slope, intercept = np.polyfit(t_v, y_v, 1)
        r2 = np.corrcoef(t_v, y_v)[0, 1]**2
        
        # 2. Local Differential Inversion
        # Smooth y_v slightly to filter noise but preserve profile gradient
        window = max(5, len(y_v) // 10) # Reduced from //5 to preserve slope changes
        if window % 2 == 0: window += 1
        y_smooth = savgol_filter(y_v, window, 2)
        dy_dt = np.gradient(y_smooth, t_v)
        
        # A(L) calculation.
        areas = -(4.0 * Q / c) / np.clip(dy_dt, -1.0, -1e-8)
        radii_differential = np.sqrt(np.clip(areas / np.pi, 0.003**2, 0.20**2))
        
        # 3. Improved Height Estimation (Volumetric Balance)
        # H = (Water displacement) + (Final Air Column)
        # dz/dt = Q / A(t)
        dz_dt = Q / np.clip(areas, 1e-7, None)
        
        # Proper integration using time steps
        dt = np.diff(t_v, prepend=t_v[0])
        z_water_v = np.cumsum(dz_dt * dt)
        delta_H_water = z_water_v[-1]
        
        # Final Air Column height from final frequency
        L_eff_final = (c / 4.0) * y_v[-1]
        r_mouth = radii_differential[-1]
        L_air_final = L_eff_final - 0.6133 * r_mouth
        
        H_est = delta_H_water + L_air_final
        
        # 4. Correct Radius Mapping (Avoid Stretching)
        # We need to map z_ctrl (0 to H_est) to radii.
        z_ctrl = np.linspace(0, H_est, n_ctrl)
        radii_init = np.interp(z_ctrl, z_water_v, radii_differential, 
                               left=radii_differential[0], right=radii_differential[-1])
        
        return H_est, radii_init, r2
        
    except Exception:
        return 0.15, np.full(n_ctrl, 0.04), 0.0

# ═══════════════════════════════════════════════════════════
# Sidebar Controls
# ═══════════════════════════════════════════════════════════
st.sidebar.header("📂 1. 데이터 로드")
uploaded_file = st.sidebar.file_uploader("CSV 데이터 업로드", type=["csv"])
sound_speed = st.sidebar.number_input("소리의 속도 (m/s)", value=343.0, step=1.0)
flow_rate_ml = st.sidebar.number_input("주입 유량 (mL/s)", value=5.0, step=0.1)
temp_c = st.sidebar.number_input("온도 (°C)", value=20.0, step=0.5)

st.sidebar.header("⚙️ 2. 최적화 설정")
n_ctrl = st.sidebar.slider("형상 제어점 수", 5, 15, 8)
reg_weight = st.sidebar.slider("매끄러움 가중치", 0.0, 5.0, 1.0, 0.1)
freq_max_opt = st.sidebar.number_input("최대 주파수 (Hz)", value=5000, step=100)

st.sidebar.markdown("**모드별 가중치**")
w1 = st.sidebar.slider("f₁ 가중치", 0.0, 1.0, 1.0, 0.1)
w2 = st.sidebar.slider("f₂ 가중치", 0.0, 1.0, 0.3, 0.1)
w3 = st.sidebar.slider("f₃ 가중치", 0.0, 1.0, 0.1, 0.1)

st.sidebar.header("🧬 3. DE 파라미터")
de_maxiter = st.sidebar.slider("DE 최대 세대 수", 10, 300, 80)
de_popsize = st.sidebar.slider("DE 개체군 크기", 5, 30, 12)
de_tol = st.sidebar.number_input("DE 수렴 허용 오차", value=1e-4, format="%.1e")

st.sidebar.header("🔧 4. 실행 옵션")
log_data = st.sidebar.checkbox("🚀 최적화 과정 로그 저장 (ML용)", value=True)
skip_de_toggle = st.sidebar.checkbox("전역 탐색(DE) 건너뛰기", value=False)
run_local_polish = st.sidebar.checkbox("L-BFGS-B 정밀 최적화 추가", value=True)
use_adaptive_bounds = st.sidebar.checkbox("적응형 탐색 범위 사용", value=True, help="초기 추정값 주변으로 탐색 범위를 좁혀 속도를 높입니다.")

# ═══════════════════════════════════════════════════════════
# Main Application
# ═══════════════════════════════════════════════════════════
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # --- Column detection ---
    time_col = find_column(df, ['time_s', 'time', 't_s', 'time_sec'], required=True)
    wh_col = find_column(df, ['water_height_cm', 'water_height', 'wh_cm'])
    
    mode_cols = load_frequency_columns(df)
    if not mode_cols:
        st.error("주파수 컬럼(f_mode1_Hz 등)을 찾을 수 없습니다.")
        st.stop()
    
    # Ground truth / Profile columns
    gt_z_col = find_column(df, ['profile_z_m', 'ground_truth_z_m', 'z_m', 'z_gt'])
    gt_r_col = find_column(df, ['profile_r_m', 'ground_truth_r_m', 'target_radius_m', 'radius_m', 'r_gt'])
    flow_col = find_column(df, ['flow_rate_mLs', 'flow_rate_ml', 'flow_rate'])
    
    # --- Data extraction ---
    t_data = df[time_col].dropna().values.astype(float)
    
    # Try to get flow rate from CSV if not provided in sidebar (priority to sidebar if changed)
    csv_flow = None
    if flow_col is not None:
        csv_flow_val = df[flow_col].iloc[0]
        if np.isfinite(csv_flow_val):
            csv_flow = float(csv_flow_val)
    
    # If the user hasn't changed the default sidebar value (5.0), use CSV value if available
    if csv_flow is not None and flow_rate_ml == 5.0:
        Q = csv_flow * 1e-6
        st.sidebar.info(f"💡 CSV로부터 유량을 불러왔습니다: {csv_flow} mL/s")
    else:
        Q = flow_rate_ml * 1e-6  # m³/s
    
    medium = Air(temperature_celsius=temp_c)
    c = medium.speed_of_sound
    
    measured_freqs = {}
    n_ts = len(t_data)
    for mode_num, col_name in mode_cols.items():
        # Load and slice to match t_data length (removes padding NaNs from the profile block)
        measured_freqs[mode_num] = df[col_name].values[:n_ts].astype(float)
    
    mode_weights = {1: w1, 2: w2, 3: w3}
    
    # Ground truth / profile extraction (may have different length than t_data)
    has_gt = gt_z_col is not None and gt_r_col is not None
    if has_gt:
        gt_z = df[gt_z_col].dropna().values.astype(float)
        gt_r = df[gt_r_col].dropna().values.astype(float)
        min_len = min(len(gt_z), len(gt_r))
        gt_z = gt_z[:min_len]
        gt_r = gt_r[:min_len]
    
    # --- Data preview ---
    with st.expander("📊 데이터 미리보기", expanded=False):
        st.dataframe(df.head(10))
        st.write(f"**컬럼**: {list(df.columns)}")
        st.write(f"**모드 수**: {len(mode_cols)} ({', '.join(f'f{k}' for k in sorted(mode_cols.keys()))})")
        if has_gt:
            st.success("✅ 원본 형상 데이터 감지됨 (Ground Truth)")
        else:
            st.info("ℹ️ 원본 형상 데이터 없음 — 추정 형상만 표시됩니다")
    
    # --- Physics-informed initial estimate ---
    f1_data = measured_freqs.get(1, np.full(len(t_data), 500.0))
    H_init, radii_init, r2_init = physics_init(f1_data, t_data, Q, c, n_ctrl)
    
    # Harmonic Analysis
    cavity_type = analyze_cavity_type(measured_freqs)
    
    with st.expander("🔬 물리 기반 초기 추정 & 배수 분석", expanded=True):
        st.write(f"- 추정 형상 타입: **{cavity_type}**")
        st.write(f"- 실린더 가정 시 선형성 ($R^2$): **{r2_init*100:.1f}%**")
        st.write(f"- 추정 높이: **{H_init*100:.1f} cm**")
        st.write(f"- 바닥 반지름: **{radii_init[0]*100:.2f} cm**")
        st.write(f"- 입구 반지름: **{radii_init[-1]*100:.2f} cm**")
        
        if r2_init > 0.995:
            st.success("✅ 실린더와 거의 완벽히 일치합니다. 전역 탐색을 건너뛰어도 좋습니다.")
        elif "원뿔대" in cavity_type:
            st.info("ℹ️ 원뿔대 형태를 감지하여 비선형 프로파일로 초기화했습니다.")
    
    # --- UI Control ---
    st.sidebar.markdown("---")
    col_btn1, col_btn2 = st.sidebar.columns(2)
    start_btn = col_btn1.button("▶️ 최적화 시작", type="primary")
    reset_btn = col_btn2.button("🔄 초기화")
    
    if reset_btn:
        st.session_state.opt_running = False
        st.session_state.opt_finished = False
        st.session_state.opt_result = None
        st.session_state.best_x = None
        st.session_state.history = []
        st.rerun()
    
    # --- Layout ---
    col_shape, col_freq = st.columns([1, 1])
    
    with col_shape:
        st.markdown("### 🏗️ 추정 형상")
        shape_plot = st.empty()
        
        # Initial Preview (before optimization starts)
        if not st.session_state.opt_running and not st.session_state.opt_finished:
            try:
                geo_init = build_geometry_from_params(H_init, radii_init, n_ctrl)
                z_vis = np.linspace(0, H_init, 100)
                r_vis = [geo_init.radius_at(z) for z in z_vis]
                fig_pre, ax_pre = plt.subplots(figsize=(5, 7))
                ax_pre.plot(np.array(r_vis)*100, z_vis*100, 'g--', alpha=0.6, label="초기 추정 (Initial)")
                ax_pre.plot(-np.array(r_vis)*100, z_vis*100, 'g--', alpha=0.6)
                if has_gt:
                    ax_pre.plot(gt_r*100, gt_z*100, 'r--', lw=1, label="원본 (GT)")
                    ax_pre.plot(-gt_r*100, gt_z*100, 'r--', lw=1)
                ax_pre.set_xlim(-15, 15)
                ax_pre.set_ylim(-1, 25)
                ax_pre.set_title("최적화 전 초기 추정 형상")
                ax_pre.legend(fontsize=8)
                ax_pre.grid(True, alpha=0.3)
                shape_plot.pyplot(fig_pre)
                plt.close(fig_pre)
            except: pass

    with col_freq:
        st.markdown("### 📈 공명 주파수 매칭")
        freq_plot = st.empty()
    
    status_area = st.empty()
    progress_bar = st.empty()
    
    # --- Optimization ---
    if start_btn:
        st.session_state.opt_running = True
        st.session_state.opt_finished = False
        st.session_state.history = []
        
        x0 = np.concatenate([[H_init], radii_init])
        
        # --- Adaptive Bounds Logic ---
        if use_adaptive_bounds:
            # Physical classification based on harmonic ratios
            is_cylinder = (r2_init > 0.995) and ("실린더" in cavity_type)
            
            if is_cylinder:
                # Highly confident cylinder
                h_margin = 0.20 * H_init
                r_margin = 0.15 * np.mean(radii_init)
            elif "원뿔대" in cavity_type:
                # Detected taper - give more room to find the slope
                h_margin = 0.40 * H_init
                r_margin = 0.50 * np.mean(radii_init)
            else:
                # Complex/Unknown (Bottle, etc)
                h_margin = 0.50 * H_init
                r_margin = 0.70 * np.mean(radii_init)
            
            h_bounds = (max(0.01, H_init - h_margin), min(0.60, H_init + h_margin))
            # Individual bounds for each control point
            r_bounds_list = [(max(0.003, r - r_margin), min(0.25, r + r_margin)) for r in radii_init]
            bounds = [h_bounds] + r_bounds_list
        else:
            # Traditional wide bounds
            bounds = [(0.02, 0.50)] + [(0.005, 0.20)] * n_ctrl
        
        last_plot_time = [0.0]
        best_cost = [1e12]
        
        def plot_callback(x, cost, sim_freqs_dict, sample_indices, eval_num):
            """Real-time visualization callback."""
            now = time.time()
            if now - last_plot_time[0] < 1.0:
                return
            last_plot_time[0] = now
            
            if cost < best_cost[0]:
                best_cost[0] = cost
            
            H = x[0]
            rc = x[1:n_ctrl+1]
            
            try:
                geo = build_geometry_from_params(H, rc, n_ctrl)
                z_vis = np.linspace(0, H, 100)
                r_vis = np.array([geo.radius_at(z) for z in z_vis])
            except Exception:
                return
            
            # Shape plot
            fig1, ax1 = plt.subplots(figsize=(5, 7))
            ax1.plot(r_vis * 100, z_vis * 100, 'b-', lw=3, label="추정 형상")
            ax1.plot(-r_vis * 100, z_vis * 100, 'b-', lw=3)
            ax1.fill_betweenx(z_vis * 100, -r_vis * 100, r_vis * 100, alpha=0.1, color='blue')
            
            if has_gt:
                ax1.plot(gt_r * 100, gt_z * 100, 'r--', lw=2.5, alpha=0.8, label="원본 형상")
                ax1.plot(-gt_r * 100, gt_z * 100, 'r--', lw=2.5, alpha=0.8)
            
            # Initial guess as a reference
            try:
                geo_init = build_geometry_from_params(H_init, radii_init, n_ctrl)
                z_init_vis = np.linspace(0, H_init, 100)
                r_init_vis = [geo_init.radius_at(z) for z in z_init_vis]
                ax1.plot(np.array(r_init_vis)*100, z_init_vis*100, 'g:', lw=1, alpha=0.5, label="초기 추정")
                ax1.plot(-np.array(r_init_vis)*100, z_init_vis*100, 'g:', lw=1, alpha=0.5)
            except: pass

            # Plot control points
            z_ctrl_vis = np.linspace(0, H, n_ctrl)
            ax1.plot(rc * 100, z_ctrl_vis * 100, 'ko', ms=6, zorder=5, label="제어점")
            
            ax1.set_xlim(-15, 15)
            ax1.set_ylim(-1, max(25, H * 130))
            ax1.set_xlabel("반지름 (cm)")
            ax1.set_ylabel("높이 (cm)")
            ax1.legend(loc='upper right', fontsize=9)
            ax1.grid(True, alpha=0.3)
            ax1.set_title(f"형상 추정 (평가 #{eval_num})")
            fig1.tight_layout()
            shape_plot.pyplot(fig1)
            plt.close(fig1)
            
            # Frequency matching plot
            fig2, ax2 = plt.subplots(figsize=(6, 5))
            colors_meas = {1: 'red', 2: 'green', 3: 'purple'}
            colors_sim = {1: 'blue', 2: 'darkgreen', 3: 'darkorchid'}
            
            for mode_num in sorted(measured_freqs.keys()):
                f_m = measured_freqs[mode_num]
                valid_m = np.isfinite(f_m)
                ax2.plot(t_data[valid_m], f_m[valid_m], 'o', color=colors_meas.get(mode_num, 'gray'),
                         ms=4, alpha=0.5, label=f"f{mode_num} 측정")
                
                if mode_num in sim_freqs_dict:
                    f_s = sim_freqs_dict[mode_num]
                    valid_s = np.isfinite(f_s)
                    ax2.plot(t_data[sample_indices[valid_s]], f_s[valid_s], '-x',
                             color=colors_sim.get(mode_num, 'navy'), lw=2, ms=6,
                             label=f"f{mode_num} 시뮬")
            
            ax2.set_xlabel("시간 (s)")
            ax2.set_ylabel("공명 주파수 (Hz)")
            ax2.legend(fontsize=8, ncol=2)
            ax2.grid(True, alpha=0.3)
            ax2.set_title(f"비용: {cost:.4f} | 최적: {best_cost[0]:.4f}")
            fig2.tight_layout()
            freq_plot.pyplot(fig2)
            plt.close(fig2)
            
            status_area.info(f"🔄 최적화 진행 중... | 평가 #{eval_num} | 현재 비용: {cost:.4f} | 최소 비용: {best_cost[0]:.4f}")
        
        # Prepare log file
        log_file = None
        if log_data:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"dataset/opt_logs_{ts}.csv"
            
            n_sample_opt = 12 # Consistent with create_objective default
            
            # Header
            header = ["H"] + [f"r{i}" for i in range(n_ctrl)]
            header += [f"f1_t{i}" for i in range(n_sample_opt)]
            header += [f"f2_t{i}" for i in range(n_sample_opt)]
            header += ["cost"]
            
            os.makedirs("dataset", exist_ok=True)
            with open(log_file, 'w') as f:
                f.write(','.join(header) + '\n')

        # Build objective
        obj_fn, sample_indices = create_objective(
            t_data, measured_freqs, Q, medium, n_ctrl,
            mode_weights, reg_weight,
            n_sample=12, freq_max=freq_max_opt,
            callback_fn=plot_callback,
            log_file=log_file
        )
        
        # ─── Stage 1: Differential Evolution ───
        if not skip_de_toggle:
            status_area.info("🧬 **Stage 1/2**: Differential Evolution 전역 탐색 시작...")
            progress_bar.progress(10, text="DE 전역 탐색 중...")
            
            try:
                de_result = differential_evolution(
                    obj_fn,
                    bounds=bounds,
                    maxiter=de_maxiter,
                    popsize=de_popsize,
                    tol=de_tol,
                    mutation=(0.5, 1.5),
                    recombination=0.8,
                    seed=42,
                    init='sobol',
                    polish=False,
                    disp=False,
                    x0=x0,
                )
                
                best_x_de = de_result.x
                best_cost_de = de_result.fun
                
                status_area.success(f"✅ DE 완료 — 비용: {best_cost_de:.4f}")
                progress_bar.progress(70, text="DE 완료!")
                
            except Exception as e:
                st.error(f"DE 최적화 오류: {e}")
                st.session_state.opt_running = False
                st.stop()
        else:
            status_area.info("⏩ **Stage 1 건러뜀**: 초기 추정이 우수하여 DE를 건너뜁니다.")
            best_x_de = x0
            best_cost_de = 1e12 # Dummy
        
        # ─── Stage 2: L-BFGS-B Local Polish ───
        if run_local_polish:
            status_area.info("🔧 **Stage 2/2**: L-BFGS-B 정밀 최적화 중...")
            progress_bar.progress(75, text="L-BFGS-B 정밀 최적화 중...")
            
            try:
                local_result = minimize(
                    obj_fn,
                    best_x_de,
                    method='L-BFGS-B',
                    bounds=bounds,
                    options={'maxiter': 200, 'ftol': 1e-10},
                )
                
                if local_result.fun < best_cost_de:
                    best_x_final = local_result.x
                    best_cost_final = local_result.fun
                    status_area.success(
                        f"✅ L-BFGS-B 개선됨 — 비용: {best_cost_final:.4f} "
                        f"(DE: {best_cost_de:.4f} → LBFGS: {best_cost_final:.4f})"
                    )
                else:
                    best_x_final = best_x_de
                    best_cost_final = best_cost_de
                    status_area.info("ℹ️ L-BFGS-B: DE 결과가 이미 충분히 좋습니다.")
                    
            except Exception as e:
                st.warning(f"L-BFGS-B 경고: {e} — DE 결과 사용")
                best_x_final = best_x_de
                best_cost_final = best_cost_de
        else:
            best_x_final = best_x_de
            best_cost_final = best_cost_de
        
        progress_bar.progress(100, text="✅ 최적화 완료!")
        st.session_state.opt_finished = True
        st.session_state.opt_running = False
        st.session_state.best_x = best_x_final
        st.session_state.opt_result = {
            'cost': best_cost_final,
            'H': best_x_final[0],
            'radii': best_x_final[1:n_ctrl+1],
        }
    
    # ═══════════════════════════════════════════════════════════
    # Final Results Display
    # ═══════════════════════════════════════════════════════════
    if st.session_state.opt_finished and st.session_state.opt_result is not None:
        res = st.session_state.opt_result
        best_x = st.session_state.best_x
        
        st.markdown("---")
        st.markdown("## 🏆 최종 결과")
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("높이", f"{res['H']*100:.1f} cm")
        m2.metric("바닥 반지름", f"{res['radii'][0]*100:.2f} cm")
        m3.metric("입구 반지름", f"{res['radii'][-1]*100:.2f} cm")
        m4.metric("최종 비용", f"{res['cost']:.4f}")
        
        # Final shape comparison
        geo_final = build_geometry_from_params(res['H'], res['radii'], n_ctrl)
        z_final = np.linspace(0, res['H'], 200)
        r_final = np.array([geo_final.radius_at(z) for z in z_final])
        
        col_r1, col_r2 = st.columns([1, 1])
        
        with col_r1:
            st.markdown("### 최종 형상 비교")
            fig_final, ax_f = plt.subplots(figsize=(7, 8))
            
            # Estimated shape
            ax_f.plot(r_final * 100, z_final * 100, 'b-', lw=3, label="추정 형상")
            ax_f.plot(-r_final * 100, z_final * 100, 'b-', lw=3)
            ax_f.fill_betweenx(z_final * 100, -r_final * 100, r_final * 100, alpha=0.08, color='blue')
            
            # Bottom
            ax_f.plot([-r_final[0]*100, r_final[0]*100], [0, 0], 'b-', lw=3)
            
            # Control points
            z_ctrl_f = np.linspace(0, res['H'], n_ctrl)
            ax_f.plot(res['radii'] * 100, z_ctrl_f * 100, 'ko', ms=7, zorder=5, label="제어점")
            
            if has_gt:
                ax_f.plot(gt_r * 100, gt_z * 100, 'r--', lw=2.5, alpha=0.8, label="원본 형상 (Ground Truth)")
                ax_f.plot(-gt_r * 100, gt_z * 100, 'r--', lw=2.5, alpha=0.8)
            
            # Initial guess as reference
            try:
                geo_init = build_geometry_from_params(H_init, radii_init, n_ctrl)
                z_init_v = np.linspace(0, H_init, 200)
                r_init_v = [geo_init.radius_at(z) for z in z_init_v]
                ax_f.plot(np.array(r_init_v)*100, z_init_v*100, 'g:', lw=1.5, alpha=0.5, label="초기 추정")
                ax_f.plot(-np.array(r_init_v)*100, z_init_v*100, 'g:', lw=1.5, alpha=0.5)
            except: pass

            if has_gt:
                # Error analysis
                # Interpolate estimated radii at GT z positions
                r_est_at_gt = np.array([geo_final.radius_at(z) if z <= res['H'] else np.nan for z in gt_z])
                valid = np.isfinite(r_est_at_gt) & (gt_z <= res['H'])
                if np.sum(valid) > 0:
                    abs_err = np.abs(r_est_at_gt[valid] - gt_r[valid]) * 100
                    mean_err = np.mean(abs_err)
                    max_err = np.max(abs_err)
                    ax_f.set_title(f"평균 오차: {mean_err:.2f} cm, 최대 오차: {max_err:.2f} cm")
            
            ax_f.set_xlim(-15, 15)
            ax_f.set_ylim(-1, max(25, res['H'] * 130))
            ax_f.set_xlabel("반지름 (cm)")
            ax_f.set_ylabel("높이 (cm)")
            ax_f.legend(fontsize=10)
            ax_f.grid(True, alpha=0.3)
            ax_f.axvline(x=0, color='gray', linestyle=':', alpha=0.3)
            fig_final.tight_layout()
            st.pyplot(fig_final)
            plt.close(fig_final)
        
        with col_r2:
            st.markdown("### 최종 공명 주파수 비교")
            
            # Full evaluation with final geometry
            V_all = Q * t_data
            wh_all = volumes_to_water_heights(geo_final, V_all)
            
            with st.spinner("최종 공명 주파수 계산 중..."):
                final_sim = simulate_resonances_at_water_heights(
                    geo_final, wh_all, medium,
                    freq_min=50, freq_max=freq_max_opt, freq_points=1500
                )
            
            fig_freq_f, ax_ff = plt.subplots(figsize=(7, 6))
            colors_m = {1: 'red', 2: 'green', 3: 'purple'}
            colors_s = {1: 'blue', 2: 'darkgreen', 3: 'darkorchid'}
            
            for mode_num in sorted(measured_freqs.keys()):
                f_m = measured_freqs[mode_num]
                valid_m = np.isfinite(f_m)
                ax_ff.plot(t_data[valid_m], f_m[valid_m], 'o',
                           color=colors_m.get(mode_num, 'gray'),
                           ms=5, alpha=0.6, label=f"f{mode_num} 측정")
                
                f_s = [res[mode_num-1] if mode_num-1 < len(res) else np.nan for res in final_sim]
                f_s = np.array(f_s)
                valid_s = np.isfinite(f_s)
                ax_ff.plot(t_data[valid_s], f_s[valid_s], '-',
                           color=colors_s.get(mode_num, 'navy'),
                           lw=2, label=f"f{mode_num} 추정")
            
            ax_ff.set_xlabel("시간 (s)")
            ax_ff.set_ylabel("공명 주파수 (Hz)")
            ax_ff.legend(fontsize=9)
            ax_ff.grid(True, alpha=0.3)
            ax_ff.set_title("측정 vs 추정 공명 주파수")
            fig_freq_f.tight_layout()
            st.pyplot(fig_freq_f)
            plt.close(fig_freq_f)
        
        # Export results
        st.markdown("### 📥 결과 내보내기")
        export_z = np.linspace(0, res['H'], 50)
        export_r = np.array([geo_final.radius_at(z) for z in export_z])
        df_export = pd.DataFrame({
            'z_m': export_z,
            'estimated_radius_m': export_r,
            'z_cm': export_z * 100,
            'estimated_radius_cm': export_r * 100,
        })
        csv_out = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 추정 형상 다운로드 (CSV)",
            csv_out,
            file_name="estimated_shape.csv",
            mime="text/csv"
        )

else:
    st.info("📂 왼쪽 사이드바에서 CSV 데이터를 업로드해 주세요.")
    st.markdown("""
    ### 사용법
    1. **`app.py`** 에서 물 채움 시뮬레이션을 실행하고 CSV를 내보냅니다
    2. 해당 CSV를 이 앱에 업로드합니다
    3. 최적화 파라미터를 설정하고 **▶️ 최적화 시작** 을 클릭합니다
    
    ### 지원하는 CSV 형식
    - 필수: `time_s`, `f_mode1_Hz`
    - 선택: `f_mode2_Hz`, `f_mode3_Hz`, `water_height_cm`
    - 선택: `ground_truth_z_m`, `ground_truth_r_m` (또는 `target_radius_m`)
    """)

# Footer
st.divider()
st.caption("Inverse Shape Estimator v3.0 — Differential Evolution + L-BFGS-B | TMM Forward Model")
