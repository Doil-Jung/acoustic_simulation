"""
TMM 세그먼트 수에 따른 공명 주파수 수렴 테스트
- 세그먼트를 늘려가며 공명 주파수가 얼마나 변하는지 확인
- "진짜 값(현실)"에 수렴하는 지점을 찾음
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from core.geometry import CavityGeometry, create_cylinder, create_bottle
from core.materials import Air
from core.solver_1d import TransferMatrixSolver1D
from scipy.interpolate import interp1d

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

medium = Air(temperature_celsius=20.0)

# ===== 테스트할 형상들 =====
# 1. 단순 원통 (해석해 있음)
cyl = create_cylinder(0.20, 0.04)

# 2. 호리병 (복잡한 형상)
bottle = create_bottle(0.25, 0.05, 0.015, 0.18)

# 3. 학습 데이터와 동일한 방식으로 만든 랜덤 형상
z_ctrl = np.linspace(0, 0.20, 8)
radii = np.array([0.03, 0.04, 0.05, 0.06, 0.06, 0.04, 0.03, 0.02])
linear_interp = interp1d(z_ctrl, radii, kind='linear', fill_value='extrapolate')
custom = CavityGeometry("custom", 0.20, lambda z: max(0.005, float(linear_interp(np.clip(z, 0, 0.20)))), num_segments=100)

shapes = {
    "원통형 (H=20cm, r=4cm)": cyl,
    "호리병 (H=25cm)": bottle,
    "복잡한 형상 (8 제어점)": custom,
}

# ===== 세그먼트 수 범위 =====
seg_counts = [10, 20, 30, 50, 75, 100, 150, 200, 300, 500]

print("=" * 80)
print("TMM 세그먼트 수에 따른 공명 주파수 수렴 테스트")
print("=" * 80)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for ax, (shape_name, base_geo) in zip(axes, shapes.items()):
    print(f"\n▶ {shape_name}")
    print(f"  {'Segments':>8} | {'f1 (Hz)':>10} | {'f2 (Hz)':>10} | {'f3 (Hz)':>10} | {'Δf1':>8} | {'Δf2':>8}")
    print("  " + "-" * 70)
    
    results = {}  # seg_count -> [f1, f2, f3]
    
    for n_seg in seg_counts:
        # 세그먼트 수만 바꿔서 동일한 형상 시뮬레이션
        geo = CavityGeometry(
            name=base_geo.name,
            height=base_geo.height,
            radius_func=base_geo.radius_func,
            num_segments=n_seg,
        )
        
        solver = TransferMatrixSolver1D(medium)
        result = solver.solve(geo, freq_min=50, freq_max=5000, freq_points=2000)
        
        freqs = result.resonance_frequencies[:3]  # 상위 3개 모드
        while len(freqs) < 3:
            freqs.append(np.nan)
        results[n_seg] = freqs
        
        # 이전 대비 변화량
        if n_seg == seg_counts[0]:
            delta1, delta2 = "-", "-"
        else:
            prev = results[seg_counts[seg_counts.index(n_seg) - 1]]
            delta1 = f"{abs(freqs[0] - prev[0]):.2f}" if not np.isnan(freqs[0]) and not np.isnan(prev[0]) else "-"
            delta2 = f"{abs(freqs[1] - prev[1]):.2f}" if not np.isnan(freqs[1]) and not np.isnan(prev[1]) else "-"
        
        f1_str = f"{freqs[0]:.1f}" if not np.isnan(freqs[0]) else "N/A"
        f2_str = f"{freqs[1]:.1f}" if not np.isnan(freqs[1]) else "N/A"
        f3_str = f"{freqs[2]:.1f}" if not np.isnan(freqs[2]) else "N/A"
        
        print(f"  {n_seg:>8} | {f1_str:>10} | {f2_str:>10} | {f3_str:>10} | {delta1:>8} | {delta2:>8}")
    
    # 그래프
    segs = list(results.keys())
    for mode_i, (label, color) in enumerate(zip(['f₁', 'f₂', 'f₃'], ['red', 'blue', 'green'])):
        vals = [results[s][mode_i] for s in segs]
        ax.plot(segs, vals, 'o-', color=color, label=label, markersize=5)
    
    # 학습 데이터의 세그먼트 수 표시
    ax.axvline(x=30, color='orange', linestyle='--', alpha=0.8, label='학습데이터 (30)')
    ax.axvline(x=100, color='purple', linestyle='--', alpha=0.8, label='app.py 원통 (50~100)')
    
    ax.set_xlabel('TMM 세그먼트 수')
    ax.set_ylabel('공명 주파수 (Hz)')
    ax.set_title(shape_name)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')

fig.suptitle('TMM 세그먼트 수에 따른 공명 주파수 수렴 테스트', fontsize=14, fontweight='bold')
fig.tight_layout()
fig.savefig('tmm_convergence_test.png', dpi=150, bbox_inches='tight')
plt.show()

# ===== 스펙트럼 자체의 차이 시각화 =====
print("\n" + "=" * 80)
print("스펙트럼 모양 비교: 30 segments vs 100 segments (호리병)")
print("=" * 80)

fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

for n_seg, color, label in [(30, 'orange', '30 세그먼트 (학습 데이터)'), 
                              (100, 'blue', '100 세그먼트 (app.py)')]:
    geo = CavityGeometry("bottle", bottle.height, bottle.radius_func, num_segments=n_seg)
    solver = TransferMatrixSolver1D(medium)
    result = solver.solve(geo, freq_min=50, freq_max=5000, freq_points=500)
    
    power = np.log10(result.transfer_function + 1e-10)
    ax1.plot(result.frequencies, power, color=color, label=label, alpha=0.8, linewidth=1.5)

ax1.set_xlabel('주파수 (Hz)')
ax1.set_ylabel('log₁₀ Power')
ax1.set_title('호리병: 세그먼트 수에 따른 스펙트럼 비교 (AI가 보는 입력 데이터)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 차이 그래프
geo30 = CavityGeometry("b", bottle.height, bottle.radius_func, num_segments=30)
geo100 = CavityGeometry("b", bottle.height, bottle.radius_func, num_segments=100)
solver = TransferMatrixSolver1D(medium)
r30 = solver.solve(geo30, freq_min=50, freq_max=5000, freq_points=500)
r100 = solver.solve(geo100, freq_min=50, freq_max=5000, freq_points=500)

p30 = np.log10(r30.transfer_function + 1e-10)
p100 = np.log10(r100.transfer_function + 1e-10)
diff = p100 - p30

ax2.fill_between(r30.frequencies, diff, alpha=0.3, color='red')
ax2.plot(r30.frequencies, diff, color='red', linewidth=1)
ax2.axhline(y=0, color='black', linewidth=0.5)
ax2.set_xlabel('주파수 (Hz)')
ax2.set_ylabel('Δ log₁₀ Power (100seg - 30seg)')
ax2.set_title('AI가 보는 스펙트럼의 차이 (= AI의 혼란 원인)')
ax2.grid(True, alpha=0.3)

fig2.tight_layout()
fig2.savefig('tmm_spectrum_comparison.png', dpi=150, bbox_inches='tight')
plt.show()

# ===== 수렴 판정 =====
print("\n" + "=" * 80)
print("수렴 판정: 500 세그먼트 대비 오차")
print("=" * 80)

ref_seg = 500
for shape_name, base_geo in shapes.items():
    print(f"\n▶ {shape_name}")
    geo_ref = CavityGeometry("ref", base_geo.height, base_geo.radius_func, num_segments=ref_seg)
    solver = TransferMatrixSolver1D(medium)
    ref_result = solver.solve(geo_ref, freq_min=50, freq_max=5000, freq_points=2000)
    ref_f1 = ref_result.resonance_frequencies[0] if ref_result.resonance_frequencies else 0
    
    for n in [30, 50, 100, 200]:
        geo_test = CavityGeometry("test", base_geo.height, base_geo.radius_func, num_segments=n)
        test_result = solver.solve(geo_test, freq_min=50, freq_max=5000, freq_points=2000)
        test_f1 = test_result.resonance_frequencies[0] if test_result.resonance_frequencies else 0
        
        err = abs(test_f1 - ref_f1)
        err_pct = (err / ref_f1 * 100) if ref_f1 > 0 else 0
        print(f"  {n:>4} segments: f1={test_f1:.1f} Hz  (오차: {err:.2f} Hz = {err_pct:.3f}%)")

print(f"\n결론: 500 segments의 f1을 '수렴값(≈현실)'으로 간주")
