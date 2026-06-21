"""
ONNX Runtime 기반 경량 추론 전용 앱
- PyTorch 불필요 (onnxruntime만 사용)
- 학습 기능 없음, 추론(형상 예측)만 가능
- 기존 dl_spectrum_rnn_app.py의 Tab 2 UI를 그대로 유지
"""
import os
import glob
import numpy as np
import pandas as pd
import onnxruntime as ort
import streamlit as st
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# ONNX 모델 로더
# ---------------------------------------------------------
@st.cache_resource
def load_onnx_model(onnx_path):
    """ONNX 모델과 dataset_info를 로드합니다."""
    session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    
    info_path = onnx_path.replace('.onnx', '_info.npz')
    if not os.path.exists(info_path):
        st.error(f"메타데이터 파일을 찾을 수 없습니다: {info_path}")
        return None, None
    
    info_raw = np.load(info_path, allow_pickle=True)
    info = {k: info_raw[k].item() if info_raw[k].ndim == 0 else info_raw[k] 
            for k in info_raw.files}
    
    return session, info


def run_inference(session, info, input_spectra):
    """ONNX 모델로 형상 추론을 수행합니다."""
    # 정규화
    x_norm = (input_spectra - info['spec_min']) / (info['spec_max'] - info['spec_min'] + 1e-8)
    x_input = x_norm.astype(np.float32)[np.newaxis, ...]  # (1, 20, 500)
    
    # 60개 포먼트(다중 피크) 추출
    from scipy.signal import find_peaks
    hz_target = np.linspace(50, 5000, 500)
    peak_hz_list = []
    
    for step_data in input_spectra:
        peaks_idx, _ = find_peaks(step_data, prominence=0.05)
        if len(peaks_idx) > 0:
            sorted_idx = peaks_idx[np.argsort(step_data[peaks_idx])[::-1]][:3]
            top3_hz = hz_target[sorted_idx]
            if len(top3_hz) < 3:
                top3_hz = np.pad(top3_hz, (0, 3 - len(top3_hz)), mode='constant', constant_values=0.0)
            peak_hz_list.append(np.sort(top3_hz))
        else:
            peak_hz_list.append([hz_target[np.argmax(step_data)], 0.0, 0.0])
    
    peak_hz = np.array(peak_hz_list).flatten()
    hz_norm = (peak_hz / 5000.0).astype(np.float32)[np.newaxis, ...]  # (1, 60)
    
    # ONNX 추론
    pred_y = session.run(None, {
        'spectrum': x_input,
        'peak_hz': hz_norm
    })[0][0]  # (9,)
    
    # 역정규화
    pred_H = pred_y[0] * (info['H_max'] - info['H_min']) + info['H_min']
    pred_R = pred_y[1:] * (info['R_max'] - info['R_min']) + info['R_min']
    
    return pred_H, pred_R, x_norm


# ---------------------------------------------------------
# 형상 시각화
# ---------------------------------------------------------
def plot_shape(H, radii, title="Predicted Shape"):
    n_pts = len(radii)
    z_pts = np.linspace(0, H, n_pts)
    
    from scipy.interpolate import interp1d
    z_dense = np.linspace(0, H, 100)
    r_interp = interp1d(z_pts, radii, kind='linear', fill_value='extrapolate')(z_dense)
    r_interp = np.clip(r_interp, 0.01, 0.10)
    
    fig, ax = plt.subplots(figsize=(4, 6))
    ax.plot(r_interp, z_dense, 'b-', linewidth=2)
    ax.plot(-r_interp, z_dense, 'b-', linewidth=2)
    ax.fill_betweenx(z_dense, -r_interp, r_interp, color='blue', alpha=0.1)
    
    ax.plot(radii, z_pts, 'ro', markersize=4)
    ax.plot(-np.array(radii), z_pts, 'ro', markersize=4)
    
    ax.set_xlim(-0.12, 0.12)
    ax.set_ylim(-0.02, 0.35)
    ax.set_title(title)
    ax.set_xlabel("Radius (m)")
    ax.set_ylabel("Height (m)")
    ax.grid(True, linestyle='--', alpha=0.6)
    fig.tight_layout()
    return fig


def plot_spectrogram(x_norm):
    """입력 스펙트로그램 히트맵을 그립니다."""
    fig_spec, ax_spec = plt.subplots(figsize=(6, 2.5))
    im = ax_spec.imshow(x_norm, aspect='auto', origin='lower', cmap='plasma')
    ax_spec.set_title("Input Sequence (20 Steps x 500 Bins)")
    ax_spec.set_xlabel("Frequency Bins")
    ax_spec.set_ylabel("Time Sequence")
    plt.colorbar(im, ax=ax_spec)
    fig_spec.tight_layout()
    return fig_spec


# ---------------------------------------------------------
# Streamlit App UI
# ---------------------------------------------------------


st.title("🧠 순환 신경망(RNN/LSTM) 형상 역추적 — 경량 추론 전용")
st.markdown("""
이 앱은 **PyTorch 없이** ONNX Runtime만으로 동작하는 경량 추론 전용 버전입니다.  
학습된 모델로 스펙트럼 데이터를 분석하여 용기 형상을 예측합니다.
""")

# ---------------------------------------------------------
# 모델 선택
# ---------------------------------------------------------
# 모델 디렉토리 경로 (PyInstaller frozen 환경 대응)
if getattr(import_sys := __import__('sys'), 'frozen', False):
    _base = import_sys._MEIPASS
else:
    _base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
_model_dir = os.path.join(_base, 'dataset', 'models')

saved_models = sorted(glob.glob(os.path.join(_model_dir, '*.onnx')))
if not saved_models:
    st.error("⚠️ ONNX 모델 파일이 없습니다. `convert_to_onnx.py`를 먼저 실행하세요.")
    st.stop()

selected_model = st.selectbox("🧠 사용할 ONNX 모델 선택", options=saved_models)
session, info = load_onnx_model(selected_model)

if session is None:
    st.stop()

st.success(f"✅ 모델 로드 완료: {selected_model}")
st.markdown("---")

# ---------------------------------------------------------
# 추론 모드 선택
# ---------------------------------------------------------
eval_mode = st.radio("테스트 방식 선택", ["A. 검증 데이터셋 무작위 추출", "B. 수동 CSV 업로드 (app.py 출력물)"])

if eval_mode == "A. 검증 데이터셋 무작위 추출":
    if st.button("무작위 테스트 시연 (5개)"):
        try:
            # 데이터셋 로딩 (npz 파일에서 직접 로드)
            data_dir = os.path.join(_base, 'dataset', 'spectrum_data')
            chunk_files = sorted(glob.glob(os.path.join(data_dir, "*.npz")))
            
            if not chunk_files:
                st.error(f"'{data_dir}' 폴더에 .npz 파일이 없습니다.")
            else:
                # 첫 번째 청크에서 데이터 로드
                d = np.load(chunk_files[0])
                H_data = d['H']
                radii_data = d['radii']
                spectra_data = d['spectra']
                peak_hz_data = d['peak_hz'] if 'peak_hz' in d else np.zeros((len(H_data), 20, 3))
                
                test_indices = info.get('test_indices', [])
                if isinstance(test_indices, np.ndarray):
                    valid_indices = [idx for idx in test_indices if idx < len(H_data)]
                else:
                    valid_indices = []
                
                if len(valid_indices) >= 5:
                    indices = np.random.choice(valid_indices, 5, replace=False)
                    st.info(f"💡 Test Set에서 무작위 5개를 추출합니다.")
                else:
                    indices = np.random.choice(len(H_data), 5, replace=False)
                    st.warning("Test Set 인덱스가 부족하여 전체 데이터에서 무작위 추출합니다.")
                
                H_min, H_max = info['H_min'], info['H_max']
                R_min, R_max = info['R_min'], info['R_max']
                
                for idx in indices:
                    st.markdown("---")
                    input_spectra = spectra_data[idx]  # (20, 500)
                    
                    pred_H, pred_R, x_norm = run_inference(session, info, input_spectra)
                    
                    # 정답 역정규화
                    true_H = H_data[idx]
                    true_R = radii_data[idx]
                    
                    colA, colB, colC = st.columns([1, 1, 2])
                    with colA:
                        st.pyplot(plot_shape(true_H, true_R, title=f"정답 (True) #{idx}"))
                    with colB:
                        st.pyplot(plot_shape(pred_H, pred_R, title=f"RNN 예측 (Pred) #{idx}"))
                    with colC:
                        st.subheader("파라미터 비교")
                        err_h = abs(true_H - pred_H) * 1000
                        err_r = np.mean(np.abs(true_R - pred_R)) * 1000
                        st.write(f"**높이 오차**: {err_h:.1f} mm")
                        st.write(f"**반경 평균 오차**: {err_r:.1f} mm")
                        
                        fig_spec = plot_spectrogram(x_norm)
                        st.pyplot(fig_spec)
                        plt.close(fig_spec)
                        
        except Exception as e:
            st.error(f"테스트 중 오류 발생: {e}")

else:
    st.subheader("B. 수동 데이터 추론")
    st.write("`app.py`에서 다운받은 **`spectrum_data_xxx.csv`** 파일을 업로드하세요.")
    uploaded_file = st.file_uploader("스펙트럼 CSV 파일 업로드", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            freq_cols = [c for c in df.columns if c.startswith('freq_bin_')]
            
            if len(freq_cols) != 500:
                st.error(f"주파수 해상도가 500개가 아닙니다. (현재 {len(freq_cols)}개)")
            else:
                raw_spectra = df[freq_cols].values  # (N_steps, 500)
                
                n_steps_raw = len(raw_spectra)
                if n_steps_raw == 20:
                    input_spectra = raw_spectra
                    st.info(f"✅ 입력 데이터 {n_steps_raw}스텝 → 보간 없이 직접 사용")
                else:
                    from scipy.interpolate import interp1d
                    t_raw = np.linspace(0, 1, n_steps_raw)
                    t_target = np.linspace(0, 1, 20)
                    interpolator = interp1d(t_raw, raw_spectra, axis=0, kind='linear', fill_value='extrapolate')
                    input_spectra = interpolator(t_target)
                    st.warning(f"⚠️ 입력 데이터 {n_steps_raw}스텝 → 20스텝으로 보간 적용됨")
                
                pred_H, pred_R, x_norm = run_inference(session, info, input_spectra)
                
                # 정답 확인
                has_ground_truth = 'true_H' in df.columns
                if has_ground_truth:
                    true_H = df['true_H'].iloc[0]
                    true_R = [df[f'true_r{i}'].iloc[0] for i in range(8)]
                    
                    colA, colB, colC = st.columns([1, 1, 2])
                    with colA:
                        st.pyplot(plot_shape(true_H, true_R, title="정답 (app.py 원본)"))
                    with colB:
                        st.pyplot(plot_shape(pred_H, pred_R, title="RNN Model Prediction"))
                    with colC:
                        st.subheader("파라미터 비교")
                        err_h = abs(true_H - pred_H) * 1000
                        err_r = np.mean(np.abs(np.array(true_R) - pred_R)) * 1000
                        st.write(f"**높이 오차**: {err_h:.1f} mm")
                        st.write(f"**반경 평균 오차**: {err_r:.1f} mm")
                        st.success("스펙트럼 입력만으로 기하학적 형상 블라인드 유추 완료!")
                        
                        fig_spec = plot_spectrogram(x_norm)
                        st.pyplot(fig_spec)
                        plt.close(fig_spec)
                else:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.pyplot(plot_shape(pred_H, pred_R, title="RNN Model Prediction"))
                    with col2:
                        st.subheader("예측된 수치")
                        st.write(f"**높이 (H):** {pred_H:.4f} m")
                        for i, r in enumerate(pred_R):
                            st.write(f"**r[{i}]:** {r:.4f} m")
                        st.success("스펙트럼 시퀀스 분석 및 렌더링 완료!")
                        
                        fig_spec = plot_spectrogram(x_norm)
                        st.pyplot(fig_spec)
                        plt.close(fig_spec)
        except Exception as e:
            st.error(f"오류 발생: {e}")

# ─── Footer ───
st.divider()
st.caption("Acoustic Shape Estimator v2.0 — ONNX Runtime 경량 추론 전용 (PyTorch 불필요)")
