import numpy as np
import pandas as pd
import os

# NPZ 데이터 로드
dataset_path = os.path.join('dataset', 'acoustic_inverse_dataset.npz')
data = np.load(dataset_path)

# 데이터셋 요약 출력
print("=== 데이터셋 (ML 학습용) 구조 요약 ===")
print("포함된 데이터 항목:", data.files)
print("정답(Y) - 단면 프로파일 형태:", data['radii'].shape)        
print("입력(X) - 주파수 궤적 형태:", data['trajectories'].shape) 
print("입력(X) - 시간 축 형태:", data['times'].shape)
print("입력(X) - 유량(Q) 형태:", data['flow_rate'].shape)
print("참고(Domain) - Z축 형태:", data['z_points'].shape)

# 첫 번째 샘플(인덱스 0) 추출
sample_idx = 0
radii = data['radii'][sample_idx]
trajectories = data['trajectories'][sample_idx]
times = data['times'][sample_idx]
q_val = data['flow_rate'][sample_idx]
z_domain = data['z_points']

df = pd.DataFrame({
    'time_s': times,                       # AI에게 주어질 입력 축
    'f_mode1_Hz': trajectories[:, 0],      # AI에게 주어질 입력 힌트
    'f_mode2_Hz': trajectories[:, 1],
    'f_mode3_Hz': trajectories[:, 2],
    'target_radius_m': radii,              # AI가 맞혀야 할 정답
    'ground_truth_z_m': z_domain           # 정답이 매핑된 실제 컵 높이 기준점
})

output_csv = os.path.join('dataset', f'sample_{sample_idx}.csv')
df.to_csv(output_csv, index=False)
print(f"\n[유량 Q = {q_val} m^3/s]")
print(f"첫 번째 샘플(Sample 0) 데이터를 CSV로 내보냈습니다: {output_csv}")
