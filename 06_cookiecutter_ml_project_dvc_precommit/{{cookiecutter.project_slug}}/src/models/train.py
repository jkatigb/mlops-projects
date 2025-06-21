#!/usr/bin/env python3
"""Model training module for {{cookiecutter.project_name}}.

This module handles model training with support for multiple algorithms
and hyperparameter optimization.
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score
)
import xgboost as xgb
import lightgbm as lgb
import joblib
from datetime import datetime

{% if cookiecutter.use_mlflow == 'yes' -%}
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.lightgbm
{% endif -%}

{% if cookiecutter.use_wandb == 'yes' -%}
import wandb
{% endif -%}

from ..utils.config import load_config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Trains machine learning models with experiment tracking."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the model trainer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.model_config = config.get("model", {})
        self.training_config = config.get("training", {})
        self.model = None
        self.best_params = {}
        self.training_history = {
            "train_scores": [],
            "val_scores": [],
            "epochs": []
        }
        self.metadata = {
            "model_type": self.model_config.get("type", "random_forest"),
            "training_started": None,
            "training_completed": None,
            "training_duration": None,
            "best_score": None,
            "hyperparameters": {}
        }
        
        {% if cookiecutter.use_mlflow == 'yes' -%}
        # Initialize MLflow
        mlflow.set_experiment(config.get("mlflow", {}).get("experiment_name", "{{cookiecutter.project_slug}}"))
        {% endif -%}
        
        {% if cookiecutter.use_wandb == 'yes' -%}
        # Initialize Weights & Biases
        wandb.init(
            project=config.get("wandb", {}).get("project", "{{cookiecutter.project_slug}}"),
            config=config
        )
        {% endif -%}
    
    def get_model(self, model_type: str, hyperparameters: Dict[str, Any]) -> Any:
        """Get model instance based on type and hyperparameters.
        
        Args:
            model_type: Type of model to create
            hyperparameters: Model hyperparameters
            
        Returns:
            Model instance
        """
        if model_type == "random_forest":
            # Filter RF-specific parameters
            rf_params = {
                k: v for k, v in hyperparameters.items()
                if k in ["n_estimators", "max_depth", "min_samples_split", 
                        "min_samples_leaf", "max_features"]
            }
            
            # Determine if classification or regression
            if self._is_classification():
                return RandomForestClassifier(**rf_params, random_state=42, n_jobs=-1)
            else:
                return RandomForestRegressor(**rf_params, random_state=42, n_jobs=-1)
        
        elif model_type == "xgboost":
            # Filter XGBoost-specific parameters
            xgb_params = {
                k: v for k, v in hyperparameters.items()
                if k in ["n_estimators", "max_depth", "learning_rate", 
                        "subsample", "colsample_bytree"]
            }
            
            if self._is_classification():
                return xgb.XGBClassifier(**xgb_params, random_state=42, n_jobs=-1)
            else:
                return xgb.XGBRegressor(**xgb_params, random_state=42, n_jobs=-1)
        
        elif model_type == "lightgbm":
            # Filter LightGBM-specific parameters
            lgb_params = {
                k: v for k, v in hyperparameters.items()
                if k in ["n_estimators", "max_depth", "learning_rate", 
                        "num_leaves", "subsample", "colsample_bytree"]
            }
            
            if self._is_classification():
                return lgb.LGBMClassifier(**lgb_params, random_state=42, n_jobs=-1)
            else:
                return lgb.LGBMRegressor(**lgb_params, random_state=42, n_jobs=-1)
        
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _is_classification(self) -> bool:
        """Determine if this is a classification task."""
        # This is a simple heuristic - in practice, this should be
        # determined from the data or configuration
        return True  # Default to classification
    
    def perform_hyperparameter_search(
        self, X_train: pd.DataFrame, y_train: pd.Series,
        X_val: pd.DataFrame, y_val: pd.Series
    ) -> Tuple[Any, Dict[str, Any]]:
        """Perform hyperparameter optimization.
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
            
        Returns:
            Tuple of (best model, best parameters)
        """
        model_type = self.model_config.get("type", "random_forest")
        hyperparameters = self.model_config.get("hyperparameters", {})
        
        # Check if cross-validation is enabled
        cv_config = self.training_config.get("cross_validation", {})
        if cv_config.get("enabled", True):
            logger.info("Performing cross-validation hyperparameter search")
            
            # Create parameter grid
            param_grid = {}
            base_model = self.get_model(model_type, {})
            
            # Define search space based on model type
            if model_type == "random_forest":
                param_grid = {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [5, 10, 15, None],
                    "min_samples_split": [2, 5, 10],
                    "min_samples_leaf": [1, 2, 4]
                }
            elif model_type == "xgboost":
                param_grid = {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [3, 6, 9],
                    "learning_rate": [0.01, 0.1, 0.3],
                    "subsample": [0.7, 0.8, 0.9]
                }
            
            # Perform grid search
            n_splits = cv_config.get("n_splits", 5)
            scoring = "accuracy" if self._is_classification() else "neg_mean_squared_error"
            
            grid_search = GridSearchCV(
                base_model,
                param_grid,
                cv=n_splits,
                scoring=scoring,
                n_jobs=-1,
                verbose=1
            )
            
            grid_search.fit(X_train, y_train)
            
            best_model = grid_search.best_estimator_
            self.best_params = grid_search.best_params_
            
            logger.info(f"Best parameters: {self.best_params}")
            logger.info(f"Best CV score: {grid_search.best_score_}")
            
        else:
            # Use provided hyperparameters directly
            logger.info("Training with provided hyperparameters")
            best_model = self.get_model(model_type, hyperparameters)
            best_model.fit(X_train, y_train)
            self.best_params = hyperparameters
        
        return best_model, self.best_params
    
    def evaluate_model(
        self, model: Any, X: pd.DataFrame, y: pd.Series, dataset_name: str
    ) -> Dict[str, float]:
        """Evaluate model performance.
        
        Args:
            model: Trained model
            X: Features
            y: Target
            dataset_name: Name of the dataset (train/val/test)
            
        Returns:
            Dictionary of metrics
        """
        predictions = model.predict(X)
        
        if self._is_classification():
            metrics = {
                f"{dataset_name}_accuracy": accuracy_score(y, predictions),
                f"{dataset_name}_precision": precision_score(y, predictions, average="weighted"),
                f"{dataset_name}_recall": recall_score(y, predictions, average="weighted"),
                f"{dataset_name}_f1": f1_score(y, predictions, average="weighted")
            }
        else:
            metrics = {
                f"{dataset_name}_mse": mean_squared_error(y, predictions),
                f"{dataset_name}_mae": mean_absolute_error(y, predictions),
                f"{dataset_name}_r2": r2_score(y, predictions)
            }
        
        return metrics
    
    def train(
        self, input_path: Path, model_path: Path
    ) -> Dict[str, Any]:
        """Train the model.
        
        Args:
            input_path: Path to feature data
            model_path: Path to save trained model
            
        Returns:
            Training metadata
        """
        self.metadata["training_started"] = datetime.now().isoformat()
        start_time = time.time()
        
        # Load data
        logger.info("Loading feature data...")
        X_train = pd.read_parquet(input_path / "train.parquet")
        X_val = pd.read_parquet(input_path / "val.parquet")
        
        # Separate features and target
        y_train = X_train["target"]
        y_val = X_val["target"]
        X_train = X_train.drop(columns=["target"])
        X_val = X_val.drop(columns=["target"])
        
        logger.info(f"Training data shape: {X_train.shape}")
        logger.info(f"Validation data shape: {X_val.shape}")
        
        {% if cookiecutter.use_mlflow == 'yes' -%}
        # Start MLflow run
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params(self.model_config)
            mlflow.log_params(self.training_config)
            
            # Perform hyperparameter search
            self.model, self.best_params = self.perform_hyperparameter_search(
                X_train, y_train, X_val, y_val
            )
            
            # Log best parameters
            mlflow.log_params(self.best_params)
            
            # Evaluate on training and validation sets
            train_metrics = self.evaluate_model(self.model, X_train, y_train, "train")
            val_metrics = self.evaluate_model(self.model, X_val, y_val, "val")
            
            # Log metrics
            for metric_name, metric_value in {**train_metrics, **val_metrics}.items():
                mlflow.log_metric(metric_name, metric_value)
            
            # Save model
            model_path.mkdir(parents=True, exist_ok=True)
            model_file = model_path / "model.pkl"
            joblib.dump(self.model, model_file)
            
            # Log model
            mlflow.sklearn.log_model(self.model, "model")
            
            logger.info("Model training completed and logged to MLflow")
        {% else -%}
        # Perform hyperparameter search
        self.model, self.best_params = self.perform_hyperparameter_search(
            X_train, y_train, X_val, y_val
        )
        
        # Evaluate on training and validation sets
        train_metrics = self.evaluate_model(self.model, X_train, y_train, "train")
        val_metrics = self.evaluate_model(self.model, X_val, y_val, "val")
        
        # Save model
        model_path.mkdir(parents=True, exist_ok=True)
        model_file = model_path / "model.pkl"
        joblib.dump(self.model, model_file)
        
        logger.info(f"Model saved to {model_file}")
        {% endif -%}
        
        {% if cookiecutter.use_wandb == 'yes' -%}
        # Log to Weights & Biases
        wandb.log({**train_metrics, **val_metrics})
        wandb.log({"best_params": self.best_params})
        
        # Save model artifact
        artifact = wandb.Artifact("model", type="model")
        artifact.add_file(str(model_file))
        wandb.log_artifact(artifact)
        {% endif -%}
        
        # Update metadata
        self.metadata["training_completed"] = datetime.now().isoformat()
        self.metadata["training_duration"] = time.time() - start_time
        self.metadata["hyperparameters"] = self.best_params
        self.metadata["best_score"] = val_metrics.get("val_accuracy", val_metrics.get("val_r2"))
        self.metadata["metrics"] = {**train_metrics, **val_metrics}
        
        # Save training artifacts
        # Save preprocessor if it exists
        preprocessor_path = Path("data/processed/scaler.pkl")
        if preprocessor_path.exists():
            import shutil
            shutil.copy(preprocessor_path, model_path / "preprocessor.pkl")
        
        # Save feature artifacts
        feature_artifacts_path = Path("data/features/feature_artifacts.pkl")
        if feature_artifacts_path.exists():
            import shutil
            shutil.copy(feature_artifacts_path, model_path / "feature_artifacts.pkl")
        
        # Save metadata
        with open(model_path / "training_metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)
        
        # Save metrics for DVC
        metrics_file = Path("reports/training_metrics.json")
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_file, "w") as f:
            json.dump({**train_metrics, **val_metrics}, f, indent=2)
        
        return self.metadata


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train machine learning model")
    parser.add_argument("--config", type=Path, required=True, help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Train model
    trainer = ModelTrainer(config)
    metadata = trainer.train(
        Path("data/features"),
        Path("models")
    )
    
    logger.info("Model training completed successfully!")
    logger.info(f"Training duration: {metadata['training_duration']:.2f} seconds")
    logger.info(f"Best score: {metadata['best_score']:.4f}")


if __name__ == "__main__":
    main()