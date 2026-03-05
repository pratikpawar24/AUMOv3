"""
TrafficLSTM — BiLSTM + Temporal Attention for Traffic Prediction

Architecture:
  Input: [batch, seq_len, features]
    features: speed, volume, density, hour_sin, hour_cos, 
              day_sin, day_cos, is_weekend, is_holiday, road_type_enc

  Model:
    BiLSTM(128) → BiLSTM(64) → TemporalAttention → FC(64) → Output(3)
  
  Output: [predicted_speed, predicted_volume, congestion_level]

  Loss: MSE + custom congestion penalty
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple

from config import model_config


class TemporalAttention(nn.Module):
    """Attention mechanism over time steps.
    
    α_t = softmax(v^T · tanh(W·h_t + b))
    context = Σ α_t · h_t
    """
    
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn_W = nn.Linear(hidden_dim, hidden_dim, bias=True)
        self.attn_v = nn.Linear(hidden_dim, 1, bias=False)
    
    def forward(self, lstm_output: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            lstm_output: [batch, seq_len, hidden_dim]
        Returns:
            context: [batch, hidden_dim]
            attn_weights: [batch, seq_len]
        """
        energy = torch.tanh(self.attn_W(lstm_output))
        scores = self.attn_v(energy).squeeze(-1)
        attn_weights = F.softmax(scores, dim=1)
        context = torch.bmm(attn_weights.unsqueeze(1), lstm_output).squeeze(1)
        return context, attn_weights


class TrafficLSTM(nn.Module):
    """Stacked BiLSTM with Temporal Attention for traffic prediction.
    
    Architecture:
      Input Projection → BiLSTM(128) → Dropout → BiLSTM(64) → 
      TemporalAttention → FC(64) → ReLU → Dropout → FC(output_dim)
    """
    
    def __init__(
        self,
        input_dim: int = None,
        hidden_dim: int = None,
        num_layers: int = None,
        output_dim: int = None,
        dropout: float = None,
    ):
        super().__init__()
        
        self.input_dim = input_dim or model_config.input_dim
        self.hidden_dim = hidden_dim or model_config.hidden_dim
        self.num_layers = num_layers or model_config.num_layers
        self.output_dim = output_dim or model_config.output_dim
        self.dropout_rate = dropout or model_config.dropout
        
        # Input projection
        self.input_proj = nn.Linear(self.input_dim, self.hidden_dim)
        self.input_norm = nn.LayerNorm(self.hidden_dim)
        
        # Stacked BiLSTM
        self.lstm1 = nn.LSTM(
            input_size=self.hidden_dim,
            hidden_size=self.hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=0,
        )
        
        self.lstm2 = nn.LSTM(
            input_size=self.hidden_dim * 2,  # bidirectional output
            hidden_size=self.hidden_dim // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=0,
        )
        
        # Temporal Attention
        self.attention = TemporalAttention(self.hidden_dim)
        
        # Output layers
        self.dropout = nn.Dropout(self.dropout_rate)
        self.fc1 = nn.Linear(self.hidden_dim, self.hidden_dim // 2)
        self.fc2 = nn.Linear(self.hidden_dim // 2, self.output_dim)
        
        # Layer normalization
        self.norm1 = nn.LayerNorm(self.hidden_dim * 2)
        self.norm2 = nn.LayerNorm(self.hidden_dim)
        
        self._init_weights()
    
    def _init_weights(self):
        """Xavier initialization for stable training."""
        for name, param in self.named_parameters():
            if "weight_ih" in name or "weight_hh" in name:
                nn.init.xavier_uniform_(param)
            elif "bias" in name:
                nn.init.zeros_(param)
        
        nn.init.xavier_uniform_(self.fc1.weight)
        nn.init.xavier_uniform_(self.fc2.weight)
    
    def forward(
        self, x: torch.Tensor, return_attention: bool = False,
    ) -> torch.Tensor | Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.
        
        Args:
            x: [batch, seq_len, input_dim]
            return_attention: if True, also return attention weights
        
        Returns:
            predictions: [batch, output_dim]
            attn_weights: [batch, seq_len] (optional)
        """
        batch_size = x.size(0)
        
        # Input projection
        h = self.input_proj(x)
        h = self.input_norm(h)
        h = F.gelu(h)
        
        # BiLSTM Layer 1
        lstm1_out, _ = self.lstm1(h)
        lstm1_out = self.norm1(lstm1_out)
        lstm1_out = self.dropout(lstm1_out)
        
        # BiLSTM Layer 2
        lstm2_out, _ = self.lstm2(lstm1_out)
        lstm2_out = self.norm2(lstm2_out)
        lstm2_out = self.dropout(lstm2_out)
        
        # Temporal Attention
        context, attn_weights = self.attention(lstm2_out)
        
        # Output
        out = F.relu(self.fc1(context))
        out = self.dropout(out)
        predictions = self.fc2(out)
        
        # Ensure valid ranges
        # predictions[:, 0] = speed (>0)
        # predictions[:, 1] = volume (>=0)  
        # predictions[:, 2] = congestion (0-1)
        predictions = torch.cat([
            F.softplus(predictions[:, 0:1]),      # speed > 0
            F.relu(predictions[:, 1:2]),           # volume >= 0
            torch.sigmoid(predictions[:, 2:3]),    # congestion [0,1]
        ], dim=1)
        
        if return_attention:
            return predictions, attn_weights
        return predictions


class TrafficLoss(nn.Module):
    """Custom loss with congestion penalty.
    
    L = MSE(pred, target) + λ·CongestionPenalty
    CongestionPenalty = extra weight on high-congestion samples
    """
    
    def __init__(self, congestion_weight: float = 2.0):
        super().__init__()
        self.mse = nn.MSELoss(reduction="none")
        self.congestion_weight = congestion_weight
    
    def forward(
        self, predictions: torch.Tensor, targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            predictions: [batch, 3] — (speed, volume, congestion)
            targets: [batch, 3]
        """
        base_loss = self.mse(predictions, targets)
        
        # Weight congestion errors more heavily
        weights = torch.ones_like(base_loss)
        weights[:, 2] = self.congestion_weight
        
        # Extra penalty for missing high-congestion events
        high_congestion_mask = targets[:, 2] > 0.7
        weights[high_congestion_mask, 2] *= 1.5
        
        weighted_loss = (base_loss * weights).mean()
        return weighted_loss


def load_model(
    model_path: str, device: str = "cpu",
) -> TrafficLSTM:
    """Load a trained TrafficLSTM model."""
    model = TrafficLSTM()
    try:
        state_dict = torch.load(model_path, map_location=device, weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()
        print(f"[Model] Loaded TrafficLSTM from {model_path}")
    except FileNotFoundError:
        print(f"[Model] No saved model at {model_path}, using random init")
    except Exception as e:
        print(f"[Model] Error loading model: {e}, using random init")
    
    return model.to(device)


def predict_traffic(
    model: TrafficLSTM,
    features: torch.Tensor,
    device: str = "cpu",
) -> Dict[str, float]:
    """Run inference on a single feature sequence.
    
    Args:
        features: [seq_len, input_dim] or [1, seq_len, input_dim]
    
    Returns:
        {"speed": float, "volume": float, "congestion": float}
    """
    model.eval()
    
    if features.dim() == 2:
        features = features.unsqueeze(0)
    
    features = features.to(device)
    
    with torch.no_grad():
        pred = model(features)
    
    pred = pred.squeeze(0).cpu().numpy()
    
    return {
        "speed": float(pred[0]),
        "volume": float(pred[1]),
        "congestion": float(pred[2]),
    }
