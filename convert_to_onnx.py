"""
PyTorch .pt 모델을 ONNX 형식으로 변환하는 스크립트.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import torch
import torch.nn as nn
import numpy as np

# -- 모델 구조 (dl_spectrum_rnn_app.py와 동일) --
class ShapeEstimatorRNN(nn.Module):
    def __init__(self):
        super().__init__()
        input_size = 500
        hidden_dim = 256
        num_layers = 2
        
        self.lstm = nn.LSTM(
            input_size=input_size, 
            hidden_size=hidden_dim, 
            num_layers=num_layers, 
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0
        )
        
        self.fc_aux = nn.Sequential(
            nn.Linear(60, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU()
        )
        
        self.fc_seq = nn.Sequential(
            nn.Linear(hidden_dim + 64, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 9)
        )
        
    def forward(self, x_spec, x_peak):
        lstm_out, (h_n, c_n) = self.lstm(x_spec)
        last_step_out = lstm_out[:, -1, :]
        x2 = self.fc_aux(x_peak)
        x_combined = torch.cat((last_step_out, x2), dim=1)
        return self.fc_seq(x_combined)


def convert_pt_to_onnx(pt_path, onnx_path):
    print(f"[1/3] Loading model: {pt_path}")
    checkpoint = torch.load(pt_path, map_location='cpu', weights_only=False)
    
    model = ShapeEstimatorRNN()
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # dataset_info 별도 저장
    dataset_info = checkpoint['dataset_info']
    info_path = onnx_path.replace('.onnx', '_info.npz')
    np.savez(info_path, **{k: np.array(v) for k, v in dataset_info.items()})
    print(f"[2/3] Dataset info saved: {info_path}")
    
    # 더미 입력
    dummy_spec = torch.randn(1, 20, 500)
    dummy_peak = torch.randn(1, 60)
    
    # ONNX 변환 (legacy API 사용으로 호환성 확보)
    print(f"[3/3] Exporting ONNX: {onnx_path}")
    torch.onnx.export(
        model,
        (dummy_spec, dummy_peak),
        onnx_path,
        input_names=['spectrum', 'peak_hz'],
        output_names=['prediction'],
        dynamic_axes={
            'spectrum': {0: 'batch'},
            'peak_hz': {0: 'batch'},
            'prediction': {0: 'batch'}
        },
        opset_version=17,
        dynamo=False  # legacy tracer 사용 (안정적)
    )
    
    # 변환 검증
    import onnxruntime as ort
    session = ort.InferenceSession(onnx_path)
    onnx_pred = session.run(None, {
        'spectrum': dummy_spec.numpy(),
        'peak_hz': dummy_peak.numpy()
    })[0]
    
    with torch.no_grad():
        torch_pred = model(dummy_spec, dummy_peak).numpy()
    
    max_diff = np.max(np.abs(onnx_pred - torch_pred))
    print(f"\nDone! (PyTorch vs ONNX max diff: {max_diff:.8f})")
    print(f"  ONNX model: {onnx_path} ({os.path.getsize(onnx_path) / 1024 / 1024:.1f} MB)")
    print(f"  Metadata:   {info_path}")


if __name__ == "__main__":
    pt_path = "dataset/models/rnn_60formants_model.pt"
    onnx_path = "dataset/models/rnn_60formants_model.onnx"
    
    if not os.path.exists(pt_path):
        print(f"Model not found: {pt_path}")
    else:
        convert_pt_to_onnx(pt_path, onnx_path)
