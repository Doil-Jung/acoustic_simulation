import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from torch.utils.data import Dataset
import json

# ═══════════════════════════════════════════════════════════
# 1. Dataset & Preprocessing (스케일러 등)
# ═══════════════════════════════════════════════════════════
class AcousticScaler:
    """
    Inputs (Frequencies, 50~4000Hz) and Outputs (Height/Radii, 0.01~0.4m) 
    must be scaled for the neural network. We use MinMax scaling to [0, 1].
    Missing formants (0.0) remain distinct.
    """
    def __init__(self):
        # We manually define max bounds for physics normalization
        self.f_max = 4000.0
        self.h_max = 0.45    # Max generated height 0.40 + margin
        self.r_max = 0.20    # Max generated radius 0.15 + margin
        
    def transform_x(self, x):
        return x / self.f_max
        
    def transform_y(self, y):
        # y is [H, r0, r1... r7]
        y_scaled = np.zeros_like(y)
        y_scaled[..., 0] = y[..., 0] / self.h_max
        y_scaled[..., 1:] = y[..., 1:] / self.r_max
        return y_scaled
        
    def inverse_transform_y(self, y_scaled):
        y = np.zeros_like(y_scaled)
        y[..., 0] = y_scaled[..., 0] * self.h_max
        y[..., 1:] = y_scaled[..., 1:] * self.r_max
        return y


class AcousticDataset(Dataset):
    def __init__(self, csv_file, scaler=None):
        self.df = pd.read_csv(csv_file)
        
        # NaN(결측치)를 0.0으로 채워서 '포먼트가 끊겼다'는 물리적 상태를 명시적으로 학습시킴
        self.df.fillna(0.0, inplace=True)
        
        # Columns layout:
        # 0:   H
        # 1-8: r0 to r7
        # 9-28: f1_t0 to f1_t19
        # 29-48: f2_t0 to f2_t19
        # 49-68: f3_t0 to f3_t19
        # 69:  error
        
        # Extract Output (Y): H + 8 radii
        y_raw = self.df.iloc[:, 0:9].values.astype(np.float32)
        
        # Extract Input (X): 60 frequencies
        x_raw = self.df.iloc[:, 9:69].values.astype(np.float32)
        
        if scaler is None:
            self.scaler = AcousticScaler()
        else:
            self.scaler = scaler
            
        self.X = self.scaler.transform_x(x_raw)
        self.Y = self.scaler.transform_y(y_raw)
        
    def __len__(self):
        return len(self.df)
        
    def __getitem__(self, idx):
        return torch.tensor(self.X[idx]), torch.tensor(self.Y[idx])

# ═══════════════════════════════════════════════════════════
# 2. Neural Network Architecture
# ═══════════════════════════════════════════════════════════
class ShapeEstimatorMLP(nn.Module):
    def __init__(self, input_dim=60, output_dim=9):
        super(ShapeEstimatorMLP, self).__init__()
        
        # 다층 퍼셉트론 (Multi-Layer Perceptron)
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.1),
            
            nn.Linear(256, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.1),
            
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            
            nn.Linear(128, output_dim),
            nn.Sigmoid() # Scale output strictly to [0, 1] relative to defined max bounds
        )
        
    def forward(self, x):
        return self.network(x)

# Custom loss function (optional, can just use nn.MSELoss)
# Here we might want to penalize H error more than a single radius point error
class PhysicalLoss(nn.Module):
    def __init__(self, h_weight=3.0):
        super(PhysicalLoss, self).__init__()
        self.mse = nn.MSELoss(reduction='none')
        self.h_weight = h_weight
        
    def forward(self, pred, target):
        loss_matrix = self.mse(pred, target)
        
        # Apply larger penalty to Height (index 0)
        weights = torch.ones_like(pred)
        weights[:, 0] = self.h_weight 
        
        weighted_loss = loss_matrix * weights
        return weighted_loss.mean()
