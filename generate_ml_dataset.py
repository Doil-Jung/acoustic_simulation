import os
import time
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.geometry import CavityGeometry
from core.materials import Air
from core.solver_1d import TransferMatrixSolver1D

# ═══════════════════════════════════════════════════════════
# 설정 (Configuration)
# ═══════════════════════════════════════════════════════════
NUM_SAMPLES = 50000         # 생성할 데이터 개수 (밤새 2만~5만 개 권장)
NUM_CTRL_POINTS = 8         # 반지름 제어점 개수 (r0 ~ r7)
NUM_TIME_STEPS = 20         # 주파수 샘플링 개수
FILL_FRACTION = 0.90        # 물이 채워지는 최대 비율 (90%)
FLOW_RATE = 10.0 * 1e-6     # 유량 10 mL/s (고정)

H_MIN, H_MAX = 0.05, 0.30   # 컵 높이 범위 (10cm ~ 40cm)
R_MIN, R_MAX = 0.01, 0.10   # 반지름 범위 (1cm ~ 15cm)

OUTPUT_FILE = "dataset/ml_training_data_linear_50000.csv"
os.makedirs("dataset", exist_ok=True)

# ═══════════════════════════════════════════════════════════
def build_random_geometry():
    """다양한 형상(원통, 원뿔, 호리병, 커스텀)을 무작위로 생성합니다."""
    H = np.random.uniform(H_MIN, H_MAX)
    
    # 사용자 요청에 따른 2:2:2:3 비율 분배
    # cylinder: 2/9 (22.2%), cone: 2/9 (22.2%), bottle: 2/9 (22.2%), custom: 3/9 (33.3%)
    categories = ['cylinder', 'cone', 'bottle', 'custom']
    probs = [2/9, 2/9, 2/9, 3/9]
    
    shape_type = np.random.choice(categories, p=probs)
    
    if shape_type == 'cylinder':
        r_base = np.random.uniform(R_MIN, R_MAX)
        # 완벽한 11자 원통 (노이즈 제거)
        radii = np.full(NUM_CTRL_POINTS, r_base)
    
    elif shape_type == 'cone':
        # 완벽한 대각선 원뿔대 (노이즈 제거)
        r_bottom = np.random.uniform(R_MIN, R_MAX)
        r_top = np.random.uniform(R_MIN, R_MAX)
        radii = np.linspace(r_bottom, r_top, NUM_CTRL_POINTS)
        
    elif shape_type == 'bottle': 
        # 수학적인 호리병 구조 (몸통 + 좁은 목)
        # NUM_CTRL_POINTS (8개) 중 대략 아래 절반은 몸통, 위 절반은 목으로 구성
        body_r = np.random.uniform(R_MIN * 3, R_MAX)    # 몸통은 굵게
        neck_r = np.random.uniform(R_MIN, body_r * 0.6) # 목은 얇게
        
        # 목이 시작되는 지점 (1 ~ 6 사이)
        neck_start_idx = np.random.randint(2, NUM_CTRL_POINTS - 2)
        
        radii = np.zeros(NUM_CTRL_POINTS)
        radii[:neck_start_idx] = body_r
        radii[neck_start_idx:] = neck_r
        
        # 병목 직각 부분만 살짝 부드럽게 (옵션)
        smooth_idx = neck_start_idx - 1
        if smooth_idx >= 0:
            radii[smooth_idx] = (body_r + neck_r) / 2.0
            
    else: # custom 형상
        # 완전히 랜덤한 지그재그 (이전과 동일)
        base_r = np.random.uniform(R_MIN, R_MAX)
        radii = [base_r]
        for _ in range(NUM_CTRL_POINTS - 1):
            next_r = radii[-1] + np.random.normal(0, 0.03)
            radii.append(next_r)
        radii = np.array(radii)

    radii = np.clip(radii, R_MIN, R_MAX)
    
    # Piecewise Linear 구조 생성 ('꺾은 선' 보간)
    from scipy.interpolate import interp1d
    z_ctrl = np.linspace(0, H, NUM_CTRL_POINTS)
    linear_interp = interp1d(z_ctrl, radii, kind='linear', bounds_error=False, fill_value="extrapolate")
    
    def radius_func(z):
        return max(R_MIN, min(R_MAX, float(linear_interp(np.clip(z, 0, H)))))
    
    geo = CavityGeometry(
        name="random_geo",
        height=H,
        radius_func=radius_func,
        num_segments=50
    )
    return geo, H, radii

def main():
    print(f"[START] ML Data Generation (Target: {NUM_SAMPLES} samples)")
    
    medium = Air(temperature_celsius=20.0)
    solver = TransferMatrixSolver1D(medium)
    
    # 헤더 생성
    headers = ["H"] + [f"r{i}" for i in range(NUM_CTRL_POINTS)]
    for mode in [1, 2, 3]:
        headers += [f"f{mode}_t{i}" for i in range(NUM_TIME_STEPS)]
    headers += ["error"]
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(",".join(headers) + "\n")
        
    success_count = 0
    start_time = time.time()
    
    while success_count < NUM_SAMPLES:
        try:
            geo, H, radii = build_random_geometry()
            
            # 전체 부피 계산
            z_eval = np.linspace(0, H, 200)
            areas = np.array([geo.area_at(z) for z in z_eval])
            dz = H / 199
            V_cum = np.cumsum(areas * dz)
            V_cum = np.insert(V_cum, 0, 0.0)[:-1]
            total_vol = V_cum[-1]
            
            # 90%까지 차오르는 시점의 부피 및 높이 계산
            target_vol_max = total_vol * FILL_FRACTION
            volumes_sample = np.linspace(0, target_vol_max, NUM_TIME_STEPS)
            water_heights = np.interp(volumes_sample, V_cum, z_eval)
            
            f1, f2, f3 = [], [], []
            
            for wh in water_heights:
                air_height = H - wh
                if air_height < 0.01:
                    f1.append(np.nan); f2.append(np.nan); f3.append(np.nan)
                    continue
                
                # 공기 기둥
                def make_air_func(wh_val):
                    return lambda z: geo.radius_at(wh_val + z)
                
                air_geo = CavityGeometry("air", air_height, make_air_func(wh), num_segments=30)
                
                # 시뮬레이션
                result = solver.solve(air_geo, freq_min=50, freq_max=4000, freq_points=500)
                res = result.resonance_frequencies
                
                f1.append(res[0] if len(res) > 0 else np.nan)
                f2.append(res[1] if len(res) > 1 else np.nan)
                f3.append(res[2] if len(res) > 2 else np.nan)
                
            # 데이터 저장 포맷
            row = [H] + list(radii) + f1 + f2 + f3 + [0.0] # error column for compatibility
            
            # 올바르게 생성된 경우만 저장
            if np.sum(np.isfinite(f1)) > NUM_TIME_STEPS * 0.5:
                row_str = ",".join([f"{val:.6f}" if np.isfinite(val) else "NaN" for val in row])
                with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                    f.write(row_str + "\n")
                
                success_count += 1
                
                if success_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = success_count / elapsed
                    eta = (NUM_SAMPLES - success_count) / rate
                    print(f"Progress: {success_count}/{NUM_SAMPLES} | Rate: {rate:.2f} it/s | ETA: {eta/60:.1f} min")
                    
        except Exception as e:
            # 예기치 않은 오류 시 패스 (무한 생성 루프 안정을 위해)
            pass

    print(f"[DONE] Generation finished! Total {success_count} samples saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()
