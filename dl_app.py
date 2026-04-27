import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import os
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

# 커스텀 모듈
from core.ml_model import AcousticDataset, ShapeEstimatorMLP, PhysicalLoss, AcousticScaler

# 기본 설정 (한글 폰트 등)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="Deep Learning Shape Estimator", layout="wide")

st.title("🧠 Deep Learning Shape Estimator")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🏋️‍♂️ 모델 학습", "🧪 성능 평가", "🔮 실시간 추정"])

# ═══════════════════════════════════════════════════════════
# 전역 변수 및 헬퍼 함수
# ═══════════════════════════════════════════════════════════
MODEL_PATH = "dataset/ml_model.pth"

def plot_shape(H, radii, title="Predicted Shape"):
    """
    radii: [r0, ..., r7]
    H: 전체 높이
    """
    n_points = len(radii)
    y_points = np.linspace(0, H, n_points)
    
    # 꺾은 선 (Piecewise Linear) 보간
    y_dense = np.linspace(0, H, 100)
    r_dense = np.interp(y_dense, y_points, radii)
    r_dense = np.clip(r_dense, 0.001, None)
    
    fig, ax = plt.subplots(figsize=(4, 6))
    ax.plot(r_dense, y_dense, 'b-', linewidth=2, label='Profile')
    ax.plot(-r_dense, y_dense, 'b-', linewidth=2)
    ax.plot([r_dense[0], -r_dense[0]], [y_dense[0], y_dense[0]], 'b-', linewidth=2)
    ax.plot([r_dense[-1], -r_dense[-1]], [y_dense[-1], y_dense[-1]], 'b-', linewidth=2)
    
    # 제어점 표시
    ax.plot(radii, y_points, 'ro', markersize=6)
    ax.plot(-np.array(radii), y_points, 'ro', markersize=6)
    
    ax.set_title(title)
    ax.set_xlabel('Radius (m)')
    ax.set_ylabel('Height (m)')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_xlim(-0.2, 0.2)
    ax.set_ylim(-0.02, 0.45)
    return fig

# ═══════════════════════════════════════════════════════════
# TAB 1: 모델 학습 (Training)
# ═══════════════════════════════════════════════════════════
with tab1:
    st.header("1. 인공지능 모델 학습")
    
    dataset_file = st.text_input("학습 데이터셋 (CSV)", "dataset/ml_training_data_linear_50000.csv")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        epochs = st.number_input("에포크 (Epochs)", min_value=1, max_value=5000, value=100)
    with col2:
        batch_size = st.number_input("배치 크기 (Batch Size)", min_value=16, max_value=1024, value=128)
    with col3:
        lr = st.number_input("학습률 (Learning Rate)", min_value=0.0001, max_value=0.1, value=0.001, format="%.4f")
    
    use_h_weight = st.checkbox("높이(H) 가중치 부여 (Physical Loss)", value=True)
    
    if st.button("🚀 학습 시작 (Train)"):
        if not os.path.exists(dataset_file):
            st.error("데이터셋 파일을 찾을 수 없습니다!")
        else:
            with st.spinner("데이터 로딩 및 분할 중... (80% Train, 10% Val, 10% Test)"):
                full_dataset = AcousticDataset(dataset_file)
                total_len = len(full_dataset)
                
                train_len = int(total_len * 0.8)
                val_len = int(total_len * 0.1)
                test_len = total_len - train_len - val_len
                
                train_data, val_data, test_data = random_split(full_dataset, [train_len, val_len, test_len])
                
                train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
                val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)
                
                st.success(f"데이터 준비 완료! (Train: {train_len}, Val: {val_len}, Test: {test_len})")
            
            # 모델 세팅
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = ShapeEstimatorMLP().to(device)
            optimizer = optim.Adam(model.parameters(), lr=lr)
            criterion = PhysicalLoss(h_weight=3.0) if use_h_weight else nn.MSELoss()
            
            # UI 그래프 세팅
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            fig_loss, ax_loss = plt.subplots(figsize=(10, 4))
            loss_plot_placeholder = st.empty()
            
            train_losses = []
            val_losses = []
            
            # 학습 루프
            best_val_loss = float('inf')
            
            for epoch in range(epochs):
                model.train()
                running_loss = 0.0
                
                for inputs, targets in train_loader:
                    inputs, targets = inputs.to(device), targets.to(device)
                    optimizer.zero_grad()
                    outputs = model(inputs)
                    loss = criterion(outputs, targets)
                    loss.backward()
                    optimizer.step()
                    running_loss += loss.item() * inputs.size(0)
                    
                epoch_loss = running_loss / train_len
                train_losses.append(epoch_loss)
                
                # 검증 루프
                model.eval()
                val_loss = 0.0
                with torch.no_grad():
                    for inputs, targets in val_loader:
                        inputs, targets = inputs.to(device), targets.to(device)
                        outputs = model(inputs)
                        loss = criterion(outputs, targets)
                        val_loss += loss.item() * inputs.size(0)
                        
                epoch_val_loss = val_loss / val_len
                val_losses.append(epoch_val_loss)
                
                # 베스트 모델 저장
                if epoch_val_loss < best_val_loss:
                    best_val_loss = epoch_val_loss
                    torch.save(model.state_dict(), MODEL_PATH)
                
                # UI 업데이트 (10 epoch 마다)
                if epoch % max(1, epochs//10) == 0 or epoch == epochs - 1:
                    ax_loss.clear()
                    ax_loss.plot(train_losses, label='Train Loss')
                    ax_loss.plot(val_losses, label='Validation Loss')
                    ax_loss.set_title("Training Curve")
                    ax_loss.set_xlabel("Epoch")
                    ax_loss.set_ylabel("Loss")
                    ax_loss.legend()
                    ax_loss.grid(True)
                    loss_plot_placeholder.pyplot(fig_loss)
                    
                    status_text.text(f"Epoch {epoch+1}/{epochs} | Train Loss: {epoch_loss:.6f} | Val Loss: {epoch_val_loss:.6f}")
                    progress_bar.progress((epoch + 1) / epochs)
            
            st.success(f"🎉 학습 완료! 베스트 모델이 '{MODEL_PATH}'에 저장되었습니다.")

# ═══════════════════════════════════════════════════════════
# TAB 2: 성능 평가 (Validation / Test)
# ═══════════════════════════════════════════════════════════
with tab2:
    st.header("2. 모델 성능 평가")
    st.write("학습된 모델이 처음 보는 데이터를 얼마나 잘 맞추는지 확인합니다.")
    
    if st.button("무작위 테스트 데이터 시연 (5개)"):
        if not os.path.exists(MODEL_PATH):
            st.error("저장된 모델 가중치 파일(ml_model.pth)이 없습니다. 먼저 학습을 진행하세요.")
        else:
            dataset_file = "dataset/ml_training_data_linear_50000.csv"
            if not os.path.exists(dataset_file):
                st.error("데이터셋 파일이 없습니다.")
            else:
                full_dataset = AcousticDataset(dataset_file)
                model = ShapeEstimatorMLP()
                model.load_state_dict(torch.load(MODEL_PATH))
                model.eval()
                scaler = full_dataset.scaler
                
                # 랜덤하게 5개 추출
                indices = np.random.choice(len(full_dataset), 5, replace=False)
                
                for idx in indices:
                    st.markdown("---")
                    x_tensor, y_tensor = full_dataset[idx]
                    
                    with torch.no_grad():
                        pred_scaled = model(x_tensor.unsqueeze(0)).numpy()[0]
                    
                    # Inverse transform
                    pred_phys = scaler.inverse_transform_y(np.expand_dims(pred_scaled, 0))[0]
                    true_phys = scaler.inverse_transform_y(np.expand_dims(y_tensor.numpy(), 0))[0]
                    
                    colA, colB, colC = st.columns([1, 1, 2])
                    
                    with colA:
                        fig_true = plot_shape(true_phys[0], true_phys[1:], title=f"정답 (Ground Truth) #{idx}")
                        st.pyplot(fig_true)
                        
                    with colB:
                        fig_pred = plot_shape(pred_phys[0], pred_phys[1:], title=f"AI 예측 (Prediction) #{idx}")
                        st.pyplot(fig_pred)
                        
                    with colC:
                        st.subheader("파라미터 비교")
                        err_h = abs(true_phys[0] - pred_phys[0]) * 1000 # mm
                        err_r_avg = np.mean(np.abs(true_phys[1:] - pred_phys[1:])) * 1000 # mm
                        
                        st.write(f"**높이 (H):** 정답 {true_phys[0]:.4f}m vs 예측 {pred_phys[0]:.4f}m (오차: **{err_h:.1f}mm**)")
                        st.write(f"**반지름 평균 오차:** **{err_r_avg:.1f}mm**")
                        
                        df_comp = pd.DataFrame({
                            '정답(m)': true_phys[1:],
                            '예측(m)': pred_phys[1:],
                            '오차(mm)': np.abs(true_phys[1:] - pred_phys[1:]) * 1000
                        }, index=[f"r{i}" for i in range(8)])
                        st.dataframe(df_comp.style.format("{:.4f}"))

# ═══════════════════════════════════════════════════════════
# TAB 3: 실시간 추정 (Inference)
# ═══════════════════════════════════════════════════════════
with tab3:
    st.header("3. 수동 성능 평가 (0.01초 단면 추론)")
    st.write("시뮬레이션(`app.py`)에서 출력된 오디오 주파수 추적 CSV 파일을 업로드하면 즉시 형상을 렌더링하고 원본과 비교합니다.")
    
    uploaded_file = st.file_uploader("1/f 분석 CSV 파일 업로드 (예: water_filling_data.csv)", type="csv")
    
    if uploaded_file is not None:
        if not os.path.exists(MODEL_PATH):
            st.error("저장된 모델 가중치가 없습니다. 먼저 학습을 진행하세요.")
        else:
            try:
                uploaded_file.seek(0)
                df_test = pd.read_csv(uploaded_file)
                f_arrays = []
                
                # 1. 원본 형상 데이터 추출 (시각화 비교용으로만 사용)
                true_z, true_r = [], []
                if 'profile_z_m' in df_test.columns and 'profile_r_m' in df_test.columns:
                    true_z = df_test['profile_z_m'].dropna().values
                    true_r = df_test['profile_r_m'].dropna().values
                
                import scipy.interpolate as interp
                n_target = 20
                t_targets = None
                
                if 'time_s' in df_test.columns:
                    time_s_all = df_test['time_s'].dropna().values
                    max_t = time_s_all.max() if len(time_s_all) > 0 else 1.0
                    
                    # 전체 데이터를 시간 기반으로 단순히 20등분 (이전 방식 복구)
                    t_targets = np.linspace(0, max_t, n_target)
                
                if "f_mode1_Hz" in df_test.columns and 'time_s' in df_test.columns:
                    # app.py 에서 출력된 최신 포맷 (헤더 있음, 결측치 포함된 타임라인)
                    for mode_col in ['f_mode1_Hz', 'f_mode2_Hz', 'f_mode3_Hz']:
                        if mode_col in df_test.columns:
                            valid_df = df_test[['time_s', mode_col]].dropna()
                            t_arr = valid_df['time_s'].values
                            f_arr = valid_df[mode_col].values
                            if len(f_arr) > 0:
                                f_arrays.append((t_arr, f_arr))
                else:
                    # 헤더가 없는 레거시 포맷
                    uploaded_file.seek(0)
                    df_test = pd.read_csv(uploaded_file, header=None)
                    for col in range(1, min(4, len(df_test.columns))):
                        valid_data = df_test[col].dropna().values
                        if len(valid_data) > 0:
                            f_arrays.append((np.linspace(0, 1, len(valid_data)), valid_data))
                    t_targets = np.linspace(0, 1.0, n_target)
                
                # ML model inference
                x_input_raw = []
                for mode in range(3):
                    if mode < len(f_arrays) and len(f_arrays[mode][1]) > 1:
                        t_arr, f_arr = f_arrays[mode]
                        interpolator = interp.interp1d(t_arr, f_arr, kind='linear', fill_value="extrapolate")
                        f_resampled = interpolator(t_targets)
                        x_input_raw.extend(f_resampled)
                    else:
                        x_input_raw.extend(np.zeros(n_target))
                        
                x_input_raw = np.array(x_input_raw).astype(np.float32)
                
                # Normalize and infer
                scaler = AcousticScaler()
                model = ShapeEstimatorMLP()
                model.load_state_dict(torch.load(MODEL_PATH))
                model.eval()
                
                x_scaled = scaler.transform_x(np.expand_dims(x_input_raw, 0))
                x_tensor = torch.tensor(x_scaled)
                
                import time
                start_t = time.time()
                with torch.no_grad():
                    pred_scaled = model(x_tensor).numpy()[0]
                pred_phys = scaler.inverse_transform_y(np.expand_dims(pred_scaled, 0))[0]
                elapsed = time.time() - start_t
                
                st.success(f"추론 완료! (소요 시간: {elapsed:.4f} 초)")
                
                H = pred_phys[0]
                radii = pred_phys[1:]
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = plot_shape(H, radii, title="AI Predicted Shape vs True")
                    ax = fig.gca()
                    
                    # 원본 스플라인 오버레이
                    if len(true_z) > 0 and len(true_r) > 0:
                        ax.plot(true_r, true_z, 'k--', linewidth=2, label="원본 (True)", alpha=0.7)
                        ax.plot(-true_r, true_z, 'k--', linewidth=2, alpha=0.7)
                        ax.legend(loc='upper right')
                        
                    st.pyplot(fig)
                    
                with col2:
                    st.subheader("예측된 파라미터")
                    st.write(f"**전체 높이 (H):** {H:.4f} m")
                    for i, r in enumerate(radii):
                        st.write(f"**r[{i}]:** {r:.4f} m")
                
            except Exception as e:
                st.error(f"CSV 파싱 에러: {e}")
