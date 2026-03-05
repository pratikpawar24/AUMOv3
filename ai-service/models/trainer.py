"""
Model Trainer — Training loop for TrafficLSTM

Features:
  - Learning rate scheduling (OneCycleLR)
  - Early stopping with patience
  - Gradient clipping
  - Training/validation split
  - Model checkpointing
  - Metrics logging
"""

import os
import time
from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split

from models.lstm_model import TrafficLSTM, TrafficLoss
from models.data_generator import generate_dataset
from config import model_config


class Trainer:
    """Training loop for TrafficLSTM model."""
    
    def __init__(
        self,
        model: Optional[TrafficLSTM] = None,
        device: str = "cpu",
        save_dir: str = "saved_models",
    ):
        self.device = device
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        
        if model is None:
            model = TrafficLSTM()
        self.model = model.to(device)
        
        self.criterion = TrafficLoss(congestion_weight=2.0)
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=model_config.lr,
            weight_decay=1e-4,
        )
        
        self.best_val_loss = float("inf")
        self.patience_counter = 0
        self.history: Dict[str, list] = {
            "train_loss": [],
            "val_loss": [],
            "lr": [],
        }
    
    def prepare_data(
        self, num_samples: int = None, val_split: float = 0.15,
    ) -> Tuple[DataLoader, DataLoader]:
        """Generate synthetic data and create data loaders."""
        X, y = generate_dataset(num_samples=num_samples)
        
        dataset = TensorDataset(X, y)
        val_size = int(len(dataset) * val_split)
        train_size = len(dataset) - val_size
        
        train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=model_config.batch_size,
            shuffle=True,
            drop_last=True,
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=model_config.batch_size,
            shuffle=False,
        )
        
        print(f"[Trainer] Train: {train_size}, Val: {val_size}")
        return train_loader, val_loader
    
    def train_epoch(self, train_loader: DataLoader) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)
            
            self.optimizer.zero_grad()
            predictions = self.model(X_batch)
            loss = self.criterion(predictions, y_batch)
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        return total_loss / max(num_batches, 1)
    
    @torch.no_grad()
    def validate(self, val_loader: DataLoader) -> float:
        """Run validation."""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        for X_batch, y_batch in val_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)
            
            predictions = self.model(X_batch)
            loss = self.criterion(predictions, y_batch)
            
            total_loss += loss.item()
            num_batches += 1
        
        return total_loss / max(num_batches, 1)
    
    def train(
        self,
        epochs: int = None,
        num_samples: int = None,
        patience: int = 10,
    ) -> Dict[str, list]:
        """Full training loop."""
        if epochs is None:
            epochs = model_config.epochs
        
        print(f"\n{'='*60}")
        print(f"  TrafficLSTM Training — {epochs} epochs")
        print(f"  Device: {self.device}")
        print(f"{'='*60}\n")
        
        train_loader, val_loader = self.prepare_data(num_samples=num_samples)
        
        # Learning rate scheduler
        scheduler = torch.optim.lr_scheduler.OneCycleLR(
            self.optimizer,
            max_lr=model_config.lr * 3,
            epochs=epochs,
            steps_per_epoch=len(train_loader),
        )
        
        start_time = time.time()
        
        for epoch in range(1, epochs + 1):
            epoch_start = time.time()
            
            # Train
            train_loss = self.train_epoch(train_loader)
            
            # Validate
            val_loss = self.validate(val_loader)
            
            # Record
            current_lr = self.optimizer.param_groups[0]["lr"]
            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            self.history["lr"].append(current_lr)
            
            epoch_time = time.time() - epoch_start
            
            # Print progress
            if epoch % 5 == 0 or epoch == 1:
                print(
                    f"Epoch {epoch:3d}/{epochs} | "
                    f"Train: {train_loss:.6f} | "
                    f"Val: {val_loss:.6f} | "
                    f"LR: {current_lr:.6f} | "
                    f"Time: {epoch_time:.1f}s"
                )
            
            # Early stopping
            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.patience_counter = 0
                self.save_model("best_model.pt")
            else:
                self.patience_counter += 1
                if self.patience_counter >= patience:
                    print(f"\n[Trainer] Early stopping at epoch {epoch}")
                    break
            
            # Step scheduler
            try:
                scheduler.step()
            except Exception:
                pass
        
        total_time = time.time() - start_time
        print(f"\n[Trainer] Training complete in {total_time:.1f}s")
        print(f"[Trainer] Best validation loss: {self.best_val_loss:.6f}")
        
        # Save final model
        self.save_model("final_model.pt")
        
        return self.history
    
    def save_model(self, filename: str):
        """Save model state dict."""
        path = os.path.join(self.save_dir, filename)
        torch.save(self.model.state_dict(), path)
    
    def load_model(self, filename: str):
        """Load model state dict."""
        path = os.path.join(self.save_dir, filename)
        state_dict = torch.load(path, map_location=self.device, weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        print(f"[Trainer] Loaded model from {path}")


def quick_train(epochs: int = 30, samples: int = 2000) -> TrafficLSTM:
    """Quick training for demo/testing."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    trainer = Trainer(device=device)
    trainer.train(epochs=epochs, num_samples=samples, patience=8)
    return trainer.model
