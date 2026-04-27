import os
import time
import numpy as np
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.geometry import CavityGeometry
from core.materials import Air
from core.solver_1d import TransferMatrixSolver1D

# ═══════════════════════════════════════════════════════════
# 설정 (Configuration)
# ═══════════════════════════════════════════════════════════
# 커맨드라인에서 덮어쓸 수 있도록 기본값만 선언합니다.
TOTAL_SAMPLES = 50000
CHUNK_SIZE = 5000       # 5,000개 단위로 파일을 끊어서 저장 (총 10개 파일)

NUM_CTRL_POINTS = 8     # 반지름 제어점 개수 (r0 ~ r7)
NUM_TIME_STEPS = 20     # 물채움 단계
FREQ_POINTS = 500       # 주파수 해상도 (50Hz ~ 5000Hz 사이를 500등분)

FILL_FRACTION = 0.90
FLOW_RATE = 10.0 * 1e-6

H_MIN, H_MAX = 0.05, 0.30
R_MIN, R_MAX = 0.01, 0.10

OUTPUT_DIR = "dataset/spectrum_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════

def build_random_geometry():
    H = np.random.uniform(H_MIN, H_MAX)
    
    # 2:2:2:3 비율 분배
    categories = ['cylinder', 'cone', 'bottle', 'custom']
    probs = [2/9, 2/9, 2/9, 3/9]
    shape_type = np.random.choice(categories, p=probs)
    
    if shape_type == 'cylinder':
        r_base = np.random.uniform(R_MIN, R_MAX)
        radii = np.full(NUM_CTRL_POINTS, r_base)
    
    elif shape_type == 'cone':
        r_bottom = np.random.uniform(R_MIN, R_MAX)
        r_top = np.random.uniform(R_MIN, R_MAX)
        radii = np.linspace(r_bottom, r_top, NUM_CTRL_POINTS)
        
    elif shape_type == 'bottle': 
        body_r = np.random.uniform(R_MIN * 3, R_MAX)
        neck_r = np.random.uniform(R_MIN, body_r * 0.6)
        neck_start_idx = np.random.randint(2, NUM_CTRL_POINTS - 2)
        radii = np.zeros(NUM_CTRL_POINTS)
        radii[:neck_start_idx] = body_r
        radii[neck_start_idx:] = neck_r
        
        smooth_idx = neck_start_idx - 1
        if smooth_idx >= 0:
            radii[smooth_idx] = (body_r + neck_r) / 2.0
            
    else: # custom
        base_r = np.random.uniform(R_MIN, R_MAX)
        radii = [base_r]
        for _ in range(NUM_CTRL_POINTS - 1):
            next_r = radii[-1] + np.random.normal(0, 0.03)
            radii.append(next_r)
        radii = np.array(radii)

    radii = np.clip(radii, R_MIN, R_MAX)
    
    # -----------------------------------------------------
    # [데이터 증강 (Scale Augmentation) 핵심 로직]
    # 기하학적 형태(실루엣)는 완벽하게 유지한 채, 전체 절대 스케일만 랜덤하게 0.7배 ~ 1.4배 뻥튀기합니다.
    # 이를 통해 AI는 "같은 모양이라도 주파수(Hz)가 낮으면 전체 크기가 크다" 역산 법칙을 강제 학습합니다.
    scale_factor = np.random.uniform(0.7, 1.4)
    H = H * scale_factor
    radii = radii * scale_factor
    # -----------------------------------------------------
    
    from scipy.interpolate import interp1d
    z_ctrl = np.linspace(0, H, NUM_CTRL_POINTS)
    linear_interp = interp1d(z_ctrl, radii, kind='linear', bounds_error=False, fill_value="extrapolate")
    
    def radius_func(z):
        return max(R_MIN * 0.5, float(linear_interp(np.clip(z, 0, H)))) # 스케일링으로 일시적 R_MIN 하회 허용
    
    geo = CavityGeometry("random_geo", H, radius_func, num_segments=50)
    return geo, H, radii


import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate Spectrum Dataset (Multiprocessing Supported)")
    parser.add_argument("--worker_id", type=int, default=1, help="Worker ID for chunk filename prefix to avoid collisions.")
    parser.add_argument("--samples", type=int, default=TOTAL_SAMPLES, help="Number of samples this worker should generate.")
    args = parser.parse_args()
    
    worker_id = args.worker_id
    total_samples = args.samples
    
    print(f"[START] Worker {worker_id} | Data Generation (Total: {total_samples} samples in {total_samples//CHUNK_SIZE} chunks)")
    
    medium = Air(temperature_celsius=20.0)
    solver = TransferMatrixSolver1D(medium)
    
    total_generated = 0
    chunk_idx = 1
    
    start_time = time.time()
    
    while total_generated < total_samples:
        
        # 현재 청크(Chunk)에 담을 데이터 임시 저장소
        batch_H = []
        batch_radii = []
        batch_spectra = [] # (CHUNK_SIZE, 20, 500) 형태 (그림)
        batch_peak_hz = [] # (CHUNK_SIZE, 20, 3) 형태 (듀얼 인풋 포먼트 리스트)
        
        print(f"  [Worker {worker_id}] -> Building Chunk {chunk_idx}...")
        
        while len(batch_H) < CHUNK_SIZE and total_generated < total_samples:
            geo, H, radii = build_random_geometry()
            
            z_eval = np.linspace(0, H, 200)
            areas = np.array([geo.area_at(z) for z in z_eval])
            dz = H / 199
            V_cum = np.cumsum(areas * dz)
            V_cum = np.insert(V_cum, 0, 0.0)[:-1]
            total_vol = V_cum[-1]
            
            target_vol_max = total_vol * FILL_FRACTION
            volumes_sample = np.linspace(0, target_vol_max, NUM_TIME_STEPS)
            water_heights = np.interp(volumes_sample, V_cum, z_eval)
            
            spectrum_timeline = []
            peak_hz_timeline = []
            
            for wh in water_heights:
                air_height = H - wh
                if air_height < 0.01:
                    spectrum_timeline.append(np.zeros(FREQ_POINTS))
                    peak_hz_timeline.append(np.zeros(3))
                    continue
                
                def make_air_func(wh_val):
                    return lambda z: geo.radius_at(wh_val + z)
                
                air_geo = CavityGeometry("air", air_height, make_air_func(wh), num_segments=30)
                
                # 시뮬레이션: 50Hz ~ 5000Hz 범위에서 500개 샘플 추출
                result = solver.solve(air_geo, freq_min=50, freq_max=5000, freq_points=FREQ_POINTS)
                
                # TMM 응답 곡선(Transfer Function)에서 진폭(Amplitude)만 가져옴
                # 안전한 학습을 위해 로그 파워 스케일(dB 단위와 비슷하게)로 변환
                power_resp = np.log10(result.transfer_function + 1e-10)
                spectrum_timeline.append(power_resp)
                
                # [다중 포먼트 추출 (Multi-Peak Injection)] 
                # 헬름홀츠 공명에 속지 않기 위해 상위 3개의 강력한 공명 주파수(F1, F2, F3)를 추출합니다.
                from scipy.signal import find_peaks
                peaks_idx, _ = find_peaks(power_resp, prominence=0.05)
                
                if len(peaks_idx) > 0:
                    # 크기(power_resp) 순으로 내림차순 정렬하여 상위 3개 피크 추출
                    sorted_by_power = peaks_idx[np.argsort(power_resp[peaks_idx])[::-1]]
                    top3_idx = sorted_by_power[:3]
                    top3_hz = result.frequencies[top3_idx]
                    
                    # 3개가 안 될 경우 0.0 으로 패딩
                    if len(top3_hz) < 3:
                        top3_hz = np.pad(top3_hz, (0, 3 - len(top3_hz)), mode='constant', constant_values=0.0)
                        
                    # 물리적 의미인 F1, F2, F3 (저주파 -> 고주파) 순서로 정렬 확정
                    top3_hz = np.sort(top3_hz)
                    peak_hz_timeline.append(top3_hz)
                else:
                    # 극단적인 모양이라 피크가 전혀 안 잡히는 경우 단순 최대값 하나만 복사
                    best_idx = np.argmax(power_resp)
                    dominant_f = result.frequencies[best_idx]
                    peak_hz_timeline.append([dominant_f, 0.0, 0.0])
            
            spectrum_timeline = np.array(spectrum_timeline) # shape: (20, 500)
            peak_hz_timeline = np.array(peak_hz_timeline)   # shape: (20, 3)
            
            # 모드가 망가지지 않았는지 최소한의 유효성 검사 (전부 0인지)
            if np.mean(np.abs(spectrum_timeline)) > 1e-5:
                batch_H.append(H)
                batch_radii.append(radii)
                batch_spectra.append(spectrum_timeline)
                batch_peak_hz.append(peak_hz_timeline)
                
                total_generated += 1
                if total_generated % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = total_generated / elapsed
                    print(f"[Worker {worker_id}] Progress: {total_generated}/{total_samples} | Rate: {rate:.2f} it/s")

        # 하나의 청크(5,000개)가 가득 차면 Numpy 압축 포맷으로 저장
        if len(batch_H) > 0:
            out_file = os.path.join(OUTPUT_DIR, f"spectrum_chunk_w{worker_id}_{chunk_idx:03d}.npz")
            np.savez_compressed(
                out_file,
                H=np.array(batch_H, dtype=np.float32),
                radii=np.array(batch_radii, dtype=np.float32),
                spectra=np.array(batch_spectra, dtype=np.float32),
                peak_hz=np.array(batch_peak_hz, dtype=np.float32)
            )
            print(f"[SAVED] {out_file} (Samples: {len(batch_H)})")
            chunk_idx += 1

    print(f"\n[DONE] Worker {worker_id} finished generating all {total_samples} spectrum samples!")

if __name__ == "__main__":
    main()
