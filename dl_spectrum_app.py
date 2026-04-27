import os
import glob
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import streamlit as st
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# PyTorch Dataset: npz Chunk 로더
# ---------------------------------------------------------
class SpectrumDataset(Dataset):
    def __init__(self, data_dir="dataset/spectrum_data", max_samples=None):
        self.chunk_files = sorted(glob.glob(os.path.join(data_dir, "*.npz")))
        
        if not self.chunk_files:
            raise FileNotFoundError(f"'{data_dir}' 폴더에 .npz 파일이 없습니다.")
            
        self.H_data = []
        self.radii_data = []
        self.spectra_data = []
        self.peak_hz_data = []
        
        current_len = 0
        for cf in self.chunk_files:
            d = np.load(cf)
            self.H_data.append(d['H'])
            self.radii_data.append(d['radii'])
            self.spectra_data.append(d['spectra']) # shape: (N, 20, 500)
            
            # 구버전 Dataset 호환성 유지용 (peak_hz가 없는 파일 대비)
            if 'peak_hz' in d:
                self.peak_hz_data.append(d['peak_hz'])
            else:
                self.peak_hz_data.append(np.zeros((len(d['H']), 20, 3)))
                
            current_len += len(d['H'])
            if max_samples is not None and current_len >= max_samples:
                break
            
        self.H_data = np.concatenate(self.H_data, axis=0)
        self.radii_data = np.concatenate(self.radii_data, axis=0)
        self.spectra_data = np.concatenate(self.spectra_data, axis=0) # Total shape: (N, 20, 500)
        self.peak_hz_data = np.concatenate(self.peak_hz_data, axis=0) # Total shape: (N, 20, 3)
        
        if max_samples is not None and max_samples < len(self.H_data):
            self.H_data = self.H_data[:max_samples]
            self.radii_data = self.radii_data[:max_samples]
            self.spectra_data = self.spectra_data[:max_samples]
            self.peak_hz_data = self.peak_hz_data[:max_samples]
        
        # 스케일링을 위한 통계값 계산 (Min-Max 정규화)
        # 1. H & Radii 정규화 (0 ~ 1 범위)
        self.H_min, self.H_max = 0.05, 0.30
        self.R_min, self.R_max = 0.01, 0.10
        
        # 2. Spectra 정규화 (데이터셋 전체 기준)
        self.spec_min = np.min(self.spectra_data)
        self.spec_max = np.max(self.spectra_data)
        
    def __len__(self):
        return len(self.H_data)
        
    def __getitem__(self, idx):
        # 1. 입력 X 구성: (1, 20, 500) 형태의 1채널 흑백 스펙트로그램 이미지
        x = self.spectra_data[idx]
        # 정규화: (x - min) / (max - min)
        x_norm = (x - self.spec_min) / (self.spec_max - self.spec_min + 1e-8)
        
        # PyTorch CNN은 (Channel, Height, Width)를 요구하므로 채널 1 추가
        X_tensor = torch.tensor(x_norm, dtype=torch.float32).unsqueeze(0) 
        
        # 1-B. 입력 X2 구성: (60,) 형태의 다중 포먼트 주파수 수치 배열 (스케일 정보 주입)
        hz = self.peak_hz_data[idx].flatten()
        hz_norm = hz / 5000.0  # 0~5000Hz 범위이므로 정규화
        X2_tensor = torch.tensor(hz_norm, dtype=torch.float32)
        
        # 2. 정답 Y 구성: [H, r0, r1, ..., r7] (총 9개)
        h_norm = (self.H_data[idx] - self.H_min) / (self.H_max - self.H_min)
        r_norm = (self.radii_data[idx] - self.R_min) / (self.R_max - self.R_min)
        
        y = np.concatenate(([h_norm], r_norm))
        Y_tensor = torch.tensor(y, dtype=torch.float32)
        
        return X_tensor, X2_tensor, Y_tensor

# ---------------------------------------------------------
# PyTorch CNN 모델 구조 (2D Spectrum)
# ---------------------------------------------------------
class ShapeEstimatorCNN(nn.Module):
    def __init__(self):
        super().__init__()
        # 입력 형태: (Batch, Channels=1, Height=20(Steps), Width=500(Freq))
        
        # Conv Block 1
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=16, kernel_size=(3, 5), stride=1, padding=(1, 2))
        self.bn1 = nn.BatchNorm2d(16)
        self.pool1 = nn.MaxPool2d(kernel_size=(2, 4)) # -> (16, 10, 125)
        
        # Conv Block 2
        self.conv2 = nn.Conv2d(16, 32, kernel_size=(3, 5), stride=1, padding=(1, 2))
        self.bn2 = nn.BatchNorm2d(32)
        self.pool2 = nn.MaxPool2d(kernel_size=(2, 5)) # -> (32, 5, 25)
        
        # Conv Block 3
        self.conv3 = nn.Conv2d(32, 64, kernel_size=(3, 5), stride=1, padding=(1, 2))
        self.bn3 = nn.BatchNorm2d(64)
        self.pool3 = nn.MaxPool2d(kernel_size=(1, 5)) # -> (64, 5, 5)
        
        # Flatten 후 크기: 64 * 5 * 5 = 1600
        
        # Auxiliary Layer (Input 2: Peak Frequencies 보조입력용)
        # 60개의 다중 포먼트 배열을 바탕으로 절대 크기 스케일을 판단
        self.fc_aux = nn.Sequential(
            nn.Linear(60, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU()
        )
        
        # Fully Connected Layers (결합된 벡터 역산 층)
        # 1600 (모양) + 64 (절대 스케일) = 1664차원에서 출발
        self.fc_seq = nn.Sequential(
            nn.Linear(1600 + 64, 512),
            nn.ReLU(),
            nn.Dropout(0.3),  # 적극 사용하여 과적합 방지
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 9) # [H, r0~r7]
        )
        
    def forward(self, x_spec, x_peak):
        x = torch.relu(self.bn1(self.conv1(x_spec)))
        x = self.pool1(x)
        
        x = torch.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        
        x = torch.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        
        x = x.view(x.size(0), -1) # Flatten (Batch, 1600)
        
        x2 = self.fc_aux(x_peak)  # (Batch, 64)
        
        # 강제 접합 (Concatenation) : 기하학적 형태 + 절대 크기 스케일 통계
        x_combined = torch.cat((x, x2), dim=1)  # (Batch, 1664)
        
        return self.fc_seq(x_combined)

# ---------------------------------------------------------
# Streamlit App UI 로직
# ---------------------------------------------------------
st.set_page_config(page_title="Deep Learning Spectrum (CNN)", layout="wide")

st.title("🤖 심층 신경망(CNN) 기반 응답 스펙트럼 형상 역추적")
st.markdown("""
기존의 단순 Peak 추출(3개 점) 좌표를 버리고, **20단계의 시간-주파수 2D 스펙트로그램 파워 곡선**을 
통째로 CNN(합성곱 신경망) 이미지 형식으로 입력받아 노이즈 환경에서도 완벽하게 형상을 추적합니다.
(Track B: Full-Spectrum AI)
""")

if 'spec_model' not in st.session_state:
    st.session_state['spec_model'] = None
    st.session_state['spec_dataset_info'] = None
    st.session_state['last_cnn_train_plot'] = None

tab1, tab2 = st.tabs(["1. CNN 딥러닝 훈련", "2. 실전 모델 인퍼런스"])

with tab1:
    st.header("1. Full-Spectrum CNN 훈련 (Training)")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("훈련 하이퍼파라미터")
        data_dir = st.text_input("NPZ 청크 데이터 폴더", value="dataset/spectrum_data")
        batch_size = st.number_input("Batch Size", value=128, min_value=16, max_value=512)
        epochs = st.number_input("Epochs", value=30, min_value=1)
        lr = st.number_input("Learning Rate", value=0.001, format="%.4f")
        train_ratio = st.slider("Train Split (%)", 50, 95, 80)
        max_samples = st.selectbox("학습 데이터 수량 (샘플 수)", options=[5000, 10000, 50000, 100000, 150000, 200000], index=2, help="생성해둔 npz 데이터 중 일부만 잘라서 빠르게 학습을 테스트할 수 있습니다.")
        h_weight = st.number_input("높이(H) 가중치 (Height Weight)", value=5.0, min_value=1.0, max_value=20.0, step=1.0, help="형상 추론 시 절대 높이 오차에 대한 페널티를 배가하여 높이 예측 정확도를 끌어올립니다.")
        
        # 모델 저장명 지정
        st.markdown("---")
        model_save_name = st.text_input("학습 완료 후 저장할 모델 파일명 (확장자 제외)", value="cnn_60formants_model")
        
        # GPU 장치 선택 추가
        available_gpus = [f"cuda:{i}" for i in range(torch.cuda.device_count())]
        device_options = ["cpu"] + available_gpus
        selected_device = st.selectbox("학습 장치 선택 (NVIDIA는 주로 cuda:0)", options=device_options, index=1 if len(available_gpus) > 0 else 0)
        
    with col2:
        st.info("💡 **CNN 구조의 특징**\n\n결측치(Missing Peak)나 노이즈가 발생하여 곡선의 일부가 지워지더라도 가중치를 공유하는 필터가 시각적 형태를 유지하여 극강의 강건성(Robustness)을 갖습니다.")
        # 장치 정보 표시
        if "cuda" in selected_device:
            st.write(f"현재 선택된 GPU: **{torch.cuda.get_device_name(int(selected_device.split(':')[-1]))}**")
            
        start_train = st.button("🚀 CNN 모델 훈련 시작", type="primary", use_container_width=True)
        
        # 탭을 이동해도 학습 그래프가 날아가지 않도록 유지
        if st.session_state.get('last_cnn_train_plot'):
            st.markdown("### 📊 최근 학습 결과")
            st.pyplot(st.session_state['last_cnn_train_plot'])

    if start_train:
        # 모델 저장 경로 셋업
        os.makedirs("dataset/models", exist_ok=True)
        spec_model_path = f"dataset/models/{model_save_name}.pt"
        st.session_state['current_cnn_model_path'] = spec_model_path
        
        device = torch.device(selected_device)
        with st.spinner(f"데이터 로딩 및 {selected_device} 텐서 매핑 중..."):
            try:
                full_dataset = SpectrumDataset(data_dir=data_dir, max_samples=max_samples)
                total_len = len(full_dataset)
                train_len = int(total_len * (train_ratio / 100.0))
                val_len = total_len - train_len
                
                from torch.utils.data import random_split
                
                # 8:1:1 (or user defined ratio) Split
                test_val_ratio = (100.0 - train_ratio) / 2.0
                train_len = int(total_len * (train_ratio / 100.0))
                val_len = int(total_len * (test_val_ratio / 100.0))
                test_len = total_len - train_len - val_len
                
                train_data, val_data, test_data = random_split(full_dataset, [train_len, val_len, test_len])
                
                train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
                val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)
                
                # 저장 (인퍼런스에 필요한 정규화 상수 및 Test 데이터셋 인덱스 보존)
                st.session_state['spec_dataset_info'] = {
                    'H_min': full_dataset.H_min, 'H_max': full_dataset.H_max,
                    'R_min': full_dataset.R_min, 'R_max': full_dataset.R_max,
                    'spec_min': full_dataset.spec_min, 'spec_max': full_dataset.spec_max,
                    'test_indices': test_data.indices # 모델이 평생 보지 못한 10%의 데이터 인덱스 보존
                }
                
                st.success(f"CNN 데이터 분할 완료! (학습 Data: {train_len}개, 검증 Val: {val_len}개, 미확인 Test: {test_len}개)")
                
                model = ShapeEstimatorCNN().to(device)
                optimizer = optim.Adam(model.parameters(), lr=lr)
                
                loss_weights = torch.ones(9, device=device)
                loss_weights[0] = h_weight  # 인덱스 0이 전체 높이 H
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                loss_plot_placeholder = st.empty()
                fig_loss, ax_loss = plt.subplots(figsize=(10, 4))
                
                train_losses, val_losses = [], []
                best_val_loss = float('inf')
                
                for epoch in range(epochs):
                    model.train()
                    running_loss = 0.0
                    
                    for inputs_spec, inputs_peak, targets in train_loader:
                        inputs_spec = inputs_spec.to(device)
                        inputs_peak = inputs_peak.to(device)
                        targets = targets.to(device)
                        
                        optimizer.zero_grad()
                        outputs = model(inputs_spec, inputs_peak)
                        squared_errors = (outputs - targets) ** 2
                        loss = torch.mean(squared_errors * loss_weights)
                        loss.backward()
                        optimizer.step()
                        running_loss += loss.item() * inputs_spec.size(0)
                        
                    epoch_train_loss = running_loss / train_len
                    train_losses.append(epoch_train_loss)
                    
                    # 검증
                    model.eval()
                    val_loss = 0.0
                    with torch.no_grad():
                        for inputs_spec, inputs_peak, targets in val_loader:
                            inputs_spec = inputs_spec.to(device)
                            inputs_peak = inputs_peak.to(device)
                            targets = targets.to(device)
                            
                            outputs = model(inputs_spec, inputs_peak)
                            squared_errors = (outputs - targets) ** 2
                            loss = torch.mean(squared_errors * loss_weights)
                            val_loss += loss.item() * inputs_spec.size(0)
                            
                    epoch_val_loss = val_loss / val_len
                    val_losses.append(epoch_val_loss)
                    
                    # 모델 한계 돌파 시 백업 (가장 좋은 모델 저장)
                    if epoch_val_loss < best_val_loss:
                        best_val_loss = epoch_val_loss
                        torch.save({
                            'model_state_dict': model.state_dict(),
                            'dataset_info': st.session_state['spec_dataset_info']
                        }, st.session_state['spec_model_path'])
                    
                    # UI 갱신
                    progress_bar.progress((epoch + 1) / epochs)
                    status_text.text(f"Epoch [{epoch+1}/{epochs}] | Train Loss: {epoch_train_loss:.6f} | Val Loss: {epoch_val_loss:.6f}")
                    
                    ax_loss.clear()
                    ax_loss.plot(train_losses, label='Train Loss')
                    ax_loss.plot(val_losses, label='Validation Loss')
                    ax_loss.set_xlabel('Epoch')
                    ax_loss.set_ylabel('MSE Loss')
                    ax_loss.set_yscale('log')
                    ax_loss.legend()
                    loss_plot_placeholder.pyplot(fig_loss)
                    
                st.success(f"CNN 모델 학습 완료! (베스트 모델 저장됨: {st.session_state['spec_model_path']})")
                st.session_state['spec_model'] = model
                
            except Exception as e:
                st.error(f"데이터셋 로딩 실패. .npz 파일이 다 만들어졌는지 확인하세요: {str(e)}")

def plot_shape(H, radii, title="Predicted Shape"):
    n_pts = len(radii)
    z_pts = np.linspace(0, H, n_pts)
    
    from scipy.interpolate import interp1d
    z_dense = np.linspace(0, H, 100)
    
    # 꺾은선(linear) 보간 (generate_dataset과 동일한 방식 적용)
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


with tab2:
    st.header("2. 스펙트로그램 시각화 및 형상 역추적 예측")
    
    eval_mode = st.radio("테스트 방식 선택", ["A. 검증 데이터셋 무작위 추출", "B. 수동 CSV 업로드 (app.py 출력물)"])
    
    if eval_mode == "A. 검증 데이터셋 무작위 추출":
        if st.button("무작위 테스트 시연 (5개)"):
            if not os.path.exists(selected_model_path):
                st.error("선택된 CNN 모델 가중치 파일이 존재하지 않습니다. 먼저 학습(Tab 1)을 진행하세요.")
            else:
                try:
                    full_dataset = SpectrumDataset(data_dir="dataset/spectrum_data", max_samples=5000)
                    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                    
                    model = ShapeEstimatorCNN().to(device)
                    checkpoint = torch.load(selected_model_path, map_location=device, weights_only=False)
                    try:
                        model.load_state_dict(checkpoint['model_state_dict'])
                    except RuntimeError:
                        st.error("❌ **모델 구조 불일치**: 기존 모델은 '단일 인풋' 방식입니다. 현재 모델은 헬름홀츠 공명 방지용 '60포먼트 듀얼 인풋' 아키텍처이므로 **Tab 1에서 재학습**이 필수입니다.")
                        st.stop()
                    model.eval()
                    
                    info = checkpoint['dataset_info']
                    test_indices = info.get('test_indices', [])
                    
                    if len(test_indices) == 0:
                        st.warning("경고: 저장된 인덱스 정보가 없어 전체 데이터셋에서 5개를 무작위 추출합니다. (과적합 주의)")
                        indices = np.random.choice(len(full_dataset), 5, replace=False)
                    else:
                        # 5000개만 로드했는데 test_indices가 9907 등을 가리킬 수 있으므로 범위 내로 필터링
                        valid_test_indices = [idx for idx in test_indices if idx < len(full_dataset)]
                        if len(valid_test_indices) >= 5:
                            st.info(f"💡 (메모리 절약 모드 5000개 로드 중) 검증에 사용되지 않은 Test Set 배열에서 {len(valid_test_indices)}개 후보를 찾아 무작위 5개를 추출합니다.")
                            selected_subset = np.random.choice(valid_test_indices, 5, replace=False)
                            indices = selected_subset.tolist()
                        else:
                            st.warning(f"메모리 절약을 위해 데이터를 {len(full_dataset)}개만 로드하여, 해당 범위 내에 Test Set 인덱스가 부족합니다. 현재 로드된 전체 데이터에서 무작위 5개를 추출합니다.")
                            indices = np.random.choice(len(full_dataset), 5, replace=False)
                    
                    for idx in indices:
                        st.markdown("---")
                        x_tensor, x2_tensor, y_tensor = full_dataset[idx]
                        x_tensor = x_tensor.unsqueeze(0).to(device) # Batch dimension
                        x2_tensor = x2_tensor.unsqueeze(0).to(device)
                        
                        with torch.no_grad():
                            pred_y = model(x_tensor, x2_tensor).cpu().numpy()[0]
                            
                        true_y = y_tensor.numpy()
                        
                        # 역정규화 (Inverse Transform)
                        true_H = true_y[0] * (info['H_max'] - info['H_min']) + info['H_min']
                        true_R = true_y[1:] * (info['R_max'] - info['R_min']) + info['R_min']
                        
                        pred_H = pred_y[0] * (info['H_max'] - info['H_min']) + info['H_min']
                        pred_R = pred_y[1:] * (info['R_max'] - info['R_min']) + info['R_min']
                        
                        colA, colB, colC = st.columns([1, 1, 2])
                        with colA:
                            st.pyplot(plot_shape(true_H, true_R, title=f"정답 (True) #{idx}"))
                        with colB:
                            st.pyplot(plot_shape(pred_H, pred_R, title=f"CNN 예측 (Pred) #{idx}"))
                        with colC:
                            st.subheader("파라미터 비교")
                            err_h = abs(true_H - pred_H) * 1000
                            err_r = np.mean(np.abs(true_R - pred_R)) * 1000
                            st.write(f"**높이 오차**: {err_h:.1f} mm")
                            st.write(f"**반경 평균 오차**: {err_r:.1f} mm")
                            
                            # Input Spectrogram Visualization
                            fig_spec, ax_spec = plt.subplots(figsize=(6, 2.5))
                            spec_img = x_tensor.cpu().numpy()[0, 0] # (20, 500)
                            im = ax_spec.imshow(spec_img, aspect='auto', origin='lower', cmap='viridis')
                            ax_spec.set_title("Input 2D Spectrogram (20 Steps x 500 Bins)")
                            ax_spec.set_xlabel("Frequency Bins")
                            ax_spec.set_ylabel("Time Steps")
                            plt.colorbar(im, ax=ax_spec)
                            st.pyplot(fig_spec)
                            plt.close(fig_spec)
                            
                except Exception as e:
                    st.error(f"테스트 중 오류 발생: {e}")

    else:
        st.subheader("B. 수동 데이터 추론")
        st.write("`app.py`에서 다운받은 **`spectrum_data_xxx.csv`** 파일을 업로드하세요.")
        uploaded_file = st.file_uploader("스펙트럼 CSV 파일 업로드", type="csv")
        
        if uploaded_file is not None:
            if not os.path.exists(selected_model_path):
                st.error("선택된 CNN 모델 가중치가 없습니다. 먼저 학습을 진행하세요.")
            else:
                try:
                    df = pd.read_csv(uploaded_file)
                    # time_s 컬럼 제외하고 frequency bins만 추출
                    freq_cols = [c for c in df.columns if c.startswith('freq_bin_')]
                    
                    if len(freq_cols) != 500:
                        st.error(f"주파수 해상도가 500개가 아닙니다. (현재 {len(freq_cols)}개)")
                    else:
                        raw_spectra = df[freq_cols].values # shape (N_steps, 500)
                        
                        # 20단계로 보간 (Interpolation over time)
                        from scipy.interpolate import interp1d
                        n_steps_raw = len(raw_spectra)
                        t_raw = np.linspace(0, 1, n_steps_raw) 
                        t_target = np.linspace(0, 1, 20)      
                        
                        interpolator = interp1d(t_raw, raw_spectra, axis=0, kind='linear', fill_value='extrapolate')
                        input_spectra = interpolator(t_target) # shape (20, 500)
                        
                        # 모델 로드 및 전처리
                        available_gpus = [f"cuda:{i}" for i in range(torch.cuda.device_count())]
                        device_options = ["cpu"] + available_gpus
                        inf_device_name = st.selectbox("추론 장치 선택", options=device_options, index=1 if len(available_gpus) > 0 else 0)
                        device = torch.device(inf_device_name)
                        
                        checkpoint = torch.load(selected_model_path, map_location=device, weights_only=False)
                        model = ShapeEstimatorCNN().to(device)
                        try:
                            model.load_state_dict(checkpoint['model_state_dict'])
                        except RuntimeError:
                            st.error(f"❌ **모델 구조 불일치**: 현재 선택된 모델({selected_model_path})은 60포먼트 듀얼 인풋 설계와 맞지 않습니다. Tab 1에서 새로운 모델을 학습해 주세요.")
                            st.stop()
                        model.eval()
                        info = checkpoint['dataset_info']
                        
                        # 정규화
                        x_norm = (input_spectra - info['spec_min']) / (info['spec_max'] - info['spec_min'] + 1e-8)
                        x_tensor = torch.tensor(x_norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)
                        
                        # [Dual-Input] 수동 CSV 스펙트럼 배열에서 60개 포먼트(다중 피크) 추출
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
                        hz_norm = peak_hz / 5000.0
                        x2_tensor = torch.tensor(hz_norm, dtype=torch.float32).unsqueeze(0).to(device)
                        
                        # 예측
                        with torch.no_grad():
                            pred_y = model(x_tensor, x2_tensor).cpu().numpy()[0]
                            
                        pred_H = pred_y[0] * (info['H_max'] - info['H_min']) + info['H_min']
                        pred_R = pred_y[1:] * (info['R_max'] - info['R_min']) + info['R_min']
                        
                        # 컨닝 방지: AI 텐서 연산이 전부 끝난 뒤에, 시각화 검증 목적으로만 정답을 추출합니다.
                        has_ground_truth = 'true_H' in df.columns
                        if has_ground_truth:
                            true_H = df['true_H'].iloc[0]
                            true_R = [df[f'true_r{i}'].iloc[0] for i in range(8)]
                            
                            colA, colB, colC = st.columns([1, 1, 2])
                            with colA:
                                st.pyplot(plot_shape(true_H, true_R, title="정답 (app.py 원본)"))
                            with colB:
                                st.pyplot(plot_shape(pred_H, pred_R, title="CNN Model Prediction"))
                            with colC:
                                st.subheader("파라미터 비교")
                                err_h = abs(true_H - pred_H) * 1000
                                err_r = np.mean(np.abs(np.array(true_R) - pred_R)) * 1000
                                st.write(f"**높이 오차**: {err_h:.1f} mm")
                                st.write(f"**반경 평균 오차**: {err_r:.1f} mm")
                                st.success("스펙트럼 입력만으로 기하학적 형상 블라인드 유추 완료!")
                        else:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.pyplot(plot_shape(pred_H, pred_R, title="CNN Model Prediction"))
                            with col2:
                                st.subheader("예측된 수치")
                                st.write(f"**높이 (H):** {pred_H:.4f} m")
                                for i, r in enumerate(pred_R):
                                    st.write(f"**r[{i}]:** {r:.4f} m")
                                st.success("스펙트럼 분석 및 렌더링 완료!")
                except Exception as e:
                    st.error(f"오류 발생: {e}")
