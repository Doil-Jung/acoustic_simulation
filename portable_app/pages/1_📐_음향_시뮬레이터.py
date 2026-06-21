"""
Acoustic Simulation - Streamlit Application

A research tool for studying air column resonance in cavities.
Supports 1D TMM analysis and water filling simulation.
"""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add portable_app root to path (parent of pages/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.geometry import (
    CavityGeometry, create_cylinder, create_frustum, create_bottle, create_custom
)
from core.materials import Air
from core.solver_1d import TransferMatrixSolver1D
from core.water_filling import WaterFillingSim
from core.boundary import rigid_wall, radiation, velocity_source
from visualization.frequency_response import (
    plot_frequency_response, plot_impedance, plot_mode_shape,
    plot_geometry_profile, plot_water_filling_results, plot_cavity_with_water
)

# ─── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────
st.markdown('<div class="main-header">🔊 Acoustic Cavity Simulator</div>', 
            unsafe_allow_html=True)
st.markdown('<div class="sub-header">기주공명을 이용한 공동 형상 추정 연구 시뮬레이션 도구</div>', 
            unsafe_allow_html=True)

# ─── Sidebar: Medium Settings ─────────────────────────────────
with st.sidebar:
    st.header("⚙️ 매질 설정")
    temperature = st.slider("온도 (°C)", min_value=-10.0, max_value=50.0, 
                            value=20.0, step=0.5)
    medium = Air(temperature_celsius=temperature)
    
    st.info(f"**음속**: {medium.speed_of_sound:.1f} m/s\n\n"
            f"**밀도**: {medium.density:.4f} kg/m³")
    
    st.divider()
    st.header("📐 형상 설정")
    
    shape_type = st.selectbox(
        "형상 종류",
        ["원통형 (Cylinder)", "원뿔대 (Frustum)", "호리병 (Bottle)", "사용자 정의 (Custom)"]
    )
    
    if shape_type == "원통형 (Cylinder)":
        height = st.slider("높이 (cm)", 1.0, 50.0, 15.0, 0.5) / 100
        radius = st.slider("반지름 (cm)", 0.5, 10.0, 4.0, 0.1) / 100
        geometry = create_cylinder(height, radius)
        
    elif shape_type == "원뿔대 (Frustum)":
        height = st.slider("높이 (cm)", 1.0, 50.0, 15.0, 0.5) / 100
        r_bottom = st.slider("바닥 반지름 (cm)", 0.5, 10.0, 3.0, 0.1) / 100
        r_top = st.slider("입구 반지름 (cm)", 0.5, 10.0, 5.0, 0.1) / 100
        geometry = create_frustum(height, r_bottom, r_top)
        
    elif shape_type == "호리병 (Bottle)":
        height = st.slider("전체 높이 (cm)", 5.0, 50.0, 25.0, 0.5) / 100
        body_r = st.slider("몸통 반지름 (cm)", 1.0, 10.0, 5.0, 0.1) / 100
        neck_r = st.slider("목 반지름 (cm)", 0.5, 5.0, 1.5, 0.1) / 100
        neck_h = st.slider("목 시작 높이 (cm)", 3.0, 45.0, 18.0, 0.5) / 100
        geometry = create_bottle(height, body_r, neck_r, neck_h)
        
    else:  # Custom
        st.markdown("**높이별 반지름 입력** (cm)")
        custom_text = st.text_area(
            "형식: 높이, 반지름 (한 줄에 하나씩)",
            value="0, 3.0\n5, 3.5\n10, 4.0\n15, 4.5",
            height=150,
        )
        try:
            lines = [l.strip() for l in custom_text.strip().split('\n') if l.strip()]
            z_pts = []
            r_pts = []
            for line in lines:
                parts = line.split(',')
                z_pts.append(float(parts[0].strip()) / 100)
                r_pts.append(float(parts[1].strip()) / 100)
            height = z_pts[-1]
            geometry = create_custom(height, z_pts, r_pts)
        except Exception as e:
            st.error(f"입력 형식 오류: {e}")
            geometry = create_cylinder(0.15, 0.04)
    
    st.divider()
    
    # Geometry info
    vol_ml = geometry.volume() * 1e6  # m³ → mL
    st.metric("용량", f"{vol_ml:.1f} mL")

# ─── Main Area: Tabs ──────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📐 형상 미리보기", "🔬 정적 시뮬레이션", "💧 물 채움 시뮬레이션"])

# ─── Tab 1: Geometry Preview ──────────────────────────────────
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("단면 형상")
        fig_geo = plot_geometry_profile(geometry)
        st.pyplot(fig_geo, use_container_width=False)
        plt.close(fig_geo)
    
    with col2:
        st.subheader("단면적 프로파일")
        z_arr, area_arr = geometry.get_areas(200)
        
        fig_area, ax_area = plt.subplots(figsize=(8, 6))
        ax_area.plot(area_arr * 1e4, z_arr * 100, 'b-', linewidth=2)  # m² → cm²
        ax_area.set_xlabel('단면적 (cm²)')
        ax_area.set_ylabel('높이 z (cm)')
        ax_area.set_title('Cross-sectional Area Profile')
        ax_area.grid(True, alpha=0.3)
        ax_area.fill_betweenx(z_arr * 100, 0, area_arr * 1e4, alpha=0.1, color='blue')
        fig_area.tight_layout()
        st.pyplot(fig_area)
        plt.close(fig_area)

# ─── Tab 2: Static Simulation ────────────────────────────────
with tab2:
    st.subheader("1D 전달행렬법 (TMM) 시뮬레이션")
    
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        freq_min = st.number_input("최소 주파수 (Hz)", value=20, min_value=1, max_value=10000)
        freq_max = st.number_input("최대 주파수 (Hz)", value=5000, min_value=100, max_value=20000)
        freq_points = st.slider("주파수 해상도", 500, 10000, 2000, 100)
        
        # 1. Standard Cylinder Theory (Reference)
        L = geometry.height
        r_open = geometry.radius_at(L)
        end_corr = 0.6133 * r_open
        L_eff = L + end_corr
        f1_cyl = medium.speed_of_sound / (4 * L_eff)
        
        run_static = st.button("🚀 시뮬레이션 실행", type="primary", key="run_static")
        
        st.markdown("### 📚 이론적 배경")
        
        # Section 1: Cylinder
        st.info("**1. 원통형 기준 (Cylinder)**")
        st.latex(r"f_n = \frac{(2n-1)c}{4(L + \delta)}")
        st.markdown(f"- 기본 공명 ($f_1$): **{f1_cyl:.1f} Hz**")
        st.markdown(f"- 유효 길이 ($L_{{eff}}$): {L_eff*100:.2f} cm, 관구 보정 ($\delta$): {end_corr*100:.3f} cm")

        # Section 2: Frustum (if applicable)
        if shape_type == "원뿔대 (Frustum)":
            st.info("**2. 원뿔대 이론 (Frustum)**")
            st.latex(r"\tan(kL) = -kx_1")
            
            solver = TransferMatrixSolver1D(medium)
            r_bottom = geometry.radius_at(0)
            r_top = geometry.radius_at(L)
            
            f_frustum_list = solver.solve_frustum_theory(L_eff, r_bottom, r_top)
            f1_frust = f_frustum_list[0] if f_frustum_list else 0
            
            st.markdown(f"- 기본 공명 ($f_1$): **{f1_frust:.1f} Hz**")
            
            if abs(r_top - r_bottom) > 1e-6:
                x1 = r_bottom * L / (r_top - r_bottom)
                st.markdown(f"- 정점 거리 ($x_1$): {abs(x1)*100:.2f} cm")

        # Section 3: Helmholtz (if Bottle)
        if shape_type == "호리병 (Bottle)":
            st.info("**2. 헬름홀츠 공명 (Helmholtz)**")
            st.latex(r"f_H = \frac{c}{2\pi} \sqrt{\frac{S}{V L_{eff}}}")
            
            # Simplified parameters for Helmholtz
            vol_body = np.pi * (body_r**2) * neck_h
            area_neck = np.pi * (neck_r**2)
            len_neck = height - neck_h
            # Effective length of neck with end corrections at both ends 
            # (one into body, one to outside)
            l_eff_neck = len_neck + 0.6 * neck_r + 0.6 * neck_r 
            
            f_helmholtz = (medium.speed_of_sound / (2 * np.pi)) * np.sqrt(area_neck / (vol_body * l_eff_neck))
            
            st.markdown(f"- 예상 헬름홀츠 주파수 ($f_H$): **{f_helmholtz:.1f} Hz**")
            st.caption("※ 호리병의 Mode 1은 보통 헬름홀츠 공명에 해당합니다.")

            st.divider()
            st.info("**3. 결합 모드 분석 (Coupled Modes)**")
            st.markdown("고차 모드는 병 본체와 목 부분의 개별 공명 특성이 결합되어 나타납니다.")
            
            c = medium.speed_of_sound
            f_body = c / (2 * neck_h) if neck_h > 0 else 0
            f_neck = c / (2 * l_eff_neck)
            
            mc1, mc2 = st.columns(2)
            with mc1:
                st.latex(r"f_{body} = \frac{nc}{2L_{body}}")
                st.markdown(f"**병 본체 공명** (닫힌-닫힌)")
                st.markdown(f"- 1차 ($n=1$): **{f_body:.1f} Hz**")
            with mc2:
                st.latex(r"f_{neck} = \frac{nc}{2L_{neck,eff}}")
                st.markdown(f"**목 부분 공명** (열린-열린)")
                st.markdown(f"- 1차 ($n=1$): **{f_neck:.1f} Hz**")
            
            st.caption("※ 시뮬레이션의 Mode 2, 3 등은 위 두 이론값 중 하나에 가깝거나 두 특성이 혼합된 지점에서 발견됩니다.")
    
    with col_s2:
        if run_static:
            solver = TransferMatrixSolver1D(medium)
            
            with st.spinner("시뮬레이션 계산 중..."):
                result = solver.solve(geometry, 
                                      freq_min=float(freq_min),
                                      freq_max=float(freq_max),
                                      freq_points=freq_points)
            
            st.session_state['static_result'] = result
            st.session_state['static_geometry'] = geometry
        
        if 'static_result' in st.session_state:
            result = st.session_state['static_result']
            geo = st.session_state['static_geometry']
            
            # Resonance summary
            if result.resonance_frequencies:
                st.success(f"**공명 주파수 {len(result.resonance_frequencies)}개 발견**")
                
                # Use 3 columns per row to avoid truncation
                num_res = len(result.resonance_frequencies)
                for start_idx in range(0, min(num_res, 6), 3):
                    cols = st.columns(3)
                    for i in range(3):
                        idx = start_idx + i
                        if idx < num_res:
                            with cols[i]:
                                st.metric(f"Mode {idx+1}", f"{result.resonance_frequencies[idx]:.1f} Hz")
            else:
                st.warning("공명 주파수를 찾지 못했습니다. 주파수 범위를 조정해 보세요.")
            
            # Plots
            st.markdown("---")
            
            plot_tab1, plot_tab2, plot_tab3 = st.tabs(
                ["📊 주파수 응답", "📈 입력 임피던스", "🌊 모드 형상"]
            )
            
            with plot_tab1:
                fig_resp = plot_frequency_response(
                    result.frequencies, result.transfer_function,
                    result.resonance_frequencies,
                    title="Pressure Response (Bottom of Cavity)"
                )
                st.pyplot(fig_resp)
                plt.close(fig_resp)
            
            with plot_tab2:
                fig_imp = plot_impedance(
                    result.frequencies, result.impedance,
                    result.resonance_frequencies
                )
                st.pyplot(fig_imp)
                plt.close(fig_imp)
            
            with plot_tab3:
                if result.resonance_frequencies and result.mode_shapes:
                    mode_select = st.selectbox(
                        "모드 선택",
                        options=result.resonance_frequencies,
                        format_func=lambda f: f"{f:.1f} Hz",
                    )
                    if mode_select in result.mode_shapes:
                        z_mode, p_mode = result.mode_shapes[mode_select]
                        fig_mode = plot_mode_shape(
                            z_mode, p_mode, mode_select,
                            geometry_profile=geo.get_profile()
                        )
                        st.pyplot(fig_mode)
                        plt.close(fig_mode)
                else:
                    st.info("공명 주파수가 있어야 모드 형상을 볼 수 있습니다.")

# ─── Tab 3: Water Filling Simulation ─────────────────────────
with tab3:
    st.subheader("💧 물 채움 시뮬레이션")
    st.markdown("수면이 상승하며 공기 기둥의 공명 주파수가 변화하는 과정을 추적합니다.")
    
    col_w1, col_w2 = st.columns([1, 2])
    
    with col_w1:
        st.caption("⚠️ CNN/RNN 모델 추론용 CSV를 내보내려면 아래 값을 학습 데이터와 동일하게 유지하세요.")
        flow_rate_ml = st.number_input(
            "유량 (mL/s)", value=10.0, min_value=0.1, max_value=100.0, step=0.5,
            help="학습 데이터 기준: 10.0 mL/s"
        )
        flow_rate = flow_rate_ml * 1e-6  # mL/s → m³/s
        
        fill_pct = st.slider("최대 채움 비율 (%)", 10, 95, 90, 5,
                             help="학습 데이터 기준: 90%")
        num_steps = st.slider("측정 단계 수", 10, 100, 20, 5,
                              help="학습 데이터 기준: 20 단계")
        
        wf_freq_min = st.number_input("최소 주파수 (Hz)", value=50, key="wf_fmin")
        wf_freq_max = st.number_input("최대 주파수 (Hz)", value=5000, key="wf_fmax")
        
        # 학습 데이터와 불일치 경고
        mismatches = []
        if abs(flow_rate_ml - 10.0) > 0.01:
            mismatches.append(f"유량 {flow_rate_ml} mL/s (학습: 10.0)")
        if fill_pct != 90:
            mismatches.append(f"채움 비율 {fill_pct}% (학습: 90%)")
        if num_steps != 20:
            mismatches.append(f"단계 수 {num_steps} (학습: 20)")
        if wf_freq_min != 50:
            mismatches.append(f"최소 주파수 {wf_freq_min}Hz (학습: 50Hz)")
        if wf_freq_max != 5000:
            mismatches.append(f"최대 주파수 {wf_freq_max}Hz (학습: 5000Hz)")
        
        if mismatches:
            st.warning("⚠️ **학습 데이터와 불일치**\n\n" + "\n".join(f"- {m}" for m in mismatches) +
                       "\n\nCNN/RNN 모델 추론 정확도가 저하될 수 있습니다.")
        
        # Estimate fill time
        vol_fill = geometry.volume() * (fill_pct / 100)
        est_time = vol_fill / flow_rate
        st.info(f"**예상 채움 시간**: {est_time:.1f}초\n\n"
                f"**채움 부피**: {vol_fill*1e6:.1f} mL")
        
        run_water = st.button("🚀 물 채움 시뮬레이션 실행", type="primary", key="run_water")
    
    with col_w2:
        if run_water:
            sim = WaterFillingSim(medium)
            
            progress_bar = st.progress(0, text="시뮬레이션 진행 중...")
            status_text = st.empty()
            plot_placeholder = st.empty()
            
            # Run simulation as a generator
            gen = sim.simulate(
                geometry,
                flow_rate=flow_rate,
                num_steps=num_steps,
                fill_fraction=fill_pct / 100,
                freq_min=float(wf_freq_min),
                freq_max=float(wf_freq_max),
                freq_points=500,          # v2: 학습 데이터와 동일 (보간 없이 직접 500pt)
                air_num_segments=30,       # v2: 학습 데이터와 동일 (TMM 세그먼트 수)
            )
            
            for update in gen:
                if isinstance(update, tuple) and update[0] == "FINISH":
                    wf_result = update[1]
                    st.session_state['wf_result'] = wf_result
                    break
                
                step_i, wh, freqs = update
                
                # Update progress
                progress = (step_i + 1) / num_steps
                progress_bar.progress(progress, text=f"단계 {step_i+1}/{num_steps} 처리 중...")
                
                # Update visualization in real-time
                fig_fill = plot_cavity_with_water(geometry, wh)
                plot_placeholder.pyplot(fig_fill)
                plt.close(fig_fill)
                
                if freqs:
                    status_text.write(f"현재 수위: {wh*100:.1f} cm | 주요 공명: {freqs[0]:.0f} Hz")
            
            progress_bar.progress(100, text="시뮬레이션 완료!")
            status_text.empty()
            plot_placeholder.empty()
        
        if 'wf_result' in st.session_state:
            wf = st.session_state['wf_result']
            
            # Export to CSV feature
            import pandas as pd
            
            # --- CSV Export Preparation ---
            # Block 1: Time-series data (Resonances)
            max_modes = max(len(freqs) for freqs in wf.resonance_tracking) if wf.resonance_tracking else 0
            ts_data = {
                'time_s': wf.time_values,
                'water_height_cm': wf.water_heights * 100,
            }
            for m in range(max_modes):
                ts_data[f'f_mode{m+1}_Hz'] = [f[m] if m < len(f) else np.nan for f in wf.resonance_tracking]
            
            df_ts = pd.DataFrame(ts_data)
            
            # Spacer column
            df_ts['|'] = '|' 
            
            # Block 2: Static Parameters & Ground Truth Profile
            # Use higher resolution for profile to ensure accuracy in inverse solver
            n_profile = 100
            z_prof = np.linspace(0, geometry.height, n_profile)
            r_prof = np.array([geometry.radius_at(z) for z in z_prof])
            
            static_data = {
                'flow_rate_mLs': [flow_rate_ml] + [np.nan] * (n_profile - 1),
                'profile_z_m': z_prof,
                'profile_r_m': r_prof,
            }
            df_static = pd.DataFrame(static_data)
            
            # Combine them: pd.concat will pad the shorter one with NaNs
            df_export = pd.concat([df_ts, df_static], axis=1)
            csv = df_export.to_csv(index=False).encode('utf-8')
            
            # --- Block 3: Full-Spectrum Export (for CNN/RNN Models) ---
            # Save all 500 points (from 50Hz to 5000Hz) for each of the 20 time steps
            if wf.full_results and wf.full_results[0] is not None:
                spec_dict = {'time_s': wf.time_values}
                
                # 테스트 시각화 검증을 위한 정답(Ground Truth) 기록 (AI 입력 텐서와는 완전 독립됨)
                ctrl_z = np.linspace(0, geometry.height, 8)
                ctrl_r = [geometry.radius_at(z) for z in ctrl_z]
                spec_dict['true_H'] = [geometry.height] * len(wf.time_values)
                for i in range(8):
                    spec_dict[f'true_r{i}'] = [ctrl_r[i]] * len(wf.time_values)
                    
                # v2: freq_points=500, freq_min=50으로 통일했으므로 항상 500포인트
                # 보간 없이 직접 사용 (학습 데이터와 완전 동일한 파이프라인)
                for step_i, result in enumerate(wf.full_results):
                    if result is None:
                        continue
                    # log10 파워 스펙트럼 (generate_spectrum_dataset.py 와 동일 조건)
                    power_resp = np.log10(result.transfer_function + 1e-10)
                    
                    for bin_idx in range(len(power_resp)):
                        col_name = f'freq_bin_{bin_idx+1}'
                        if col_name not in spec_dict:
                            spec_dict[col_name] = []
                        spec_dict[col_name].append(power_resp[bin_idx])
                        
                df_spec = pd.DataFrame(spec_dict)
                csv_spec = df_spec.to_csv(index=False).encode('utf-8')
            else:
                csv_spec = None

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    label="📥 선형 분석 모델 (3-Peak) CSV",
                    data=csv,
                    file_name=f"water_filling_data_{geometry.name}.csv",
                    mime="text/csv",
                    help="기존의 `dl_app.py` 에 업로드할 수 있는 1차원 피크 데이터입니다."
                )
            with c2:
                if csv_spec is not None:
                    st.download_button(
                        label="📥 스펙트럼 AI 모델 (CNN/RNN) CSV",
                        data=csv_spec,
                        file_name=f"spectrum_data_{geometry.name}.csv",
                        mime="text/csv",
                        help="새로운 `dl_spectrum_app.py` 에 업로드할 수 있는 (20x500) 행렬 스펙트로그램 데이터입니다."
                    )
            
            st.divider()
            
            # Plot resonance vs water height
            st.markdown("### 수위에 따른 공명 주파수 변화")
            
            view_mode = st.radio(
                "X축 선택",
                ["수위 (cm)", "시간 (s)"],
                horizontal=True
            )
            
            fig_wf = plot_water_filling_results(
                wf.water_heights * 100,
                wf.resonance_tracking,
                time_values=wf.time_values if view_mode == "시간 (s)" else None,
            )
            st.pyplot(fig_wf)
            plt.close(fig_wf)
            
            # Show individual step details
            st.markdown("### 단계별 상세 결과")
            step_idx = st.slider("단계 선택", 0, len(wf.water_heights) - 1, 0)
            
            wh_cm = wf.water_heights[step_idx] * 100
            ah_cm = wf.air_column_heights[step_idx] * 100
            t_sec = wf.time_values[step_idx]
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("수위", f"{wh_cm:.1f} cm")
            sc2.metric("공기 기둥 높이", f"{ah_cm:.1f} cm")
            sc3.metric("경과 시간", f"{t_sec:.2f} s")
            
            if wf.resonance_tracking[step_idx]:
                st.write("**공명 주파수**: " + 
                        ", ".join(f"{f:.0f} Hz" for f in wf.resonance_tracking[step_idx]))
            
            if wf.full_results[step_idx] is not None:
                result_step = wf.full_results[step_idx]
                fig_step = plot_frequency_response(
                    result_step.frequencies, result_step.transfer_function,
                    result_step.resonance_frequencies,
                    title=f"수위 {wh_cm:.1f} cm에서의 주파수 응답"
                )
                st.pyplot(fig_step)
                plt.close(fig_step)

# ─── Footer ───────────────────────────────────────────────────
st.divider()
st.caption("Acoustic Cavity Simulator v2.0 — 학습 파이프라인 통일 (TMM 30seg, 500freq, 50Hz~5kHz)")
