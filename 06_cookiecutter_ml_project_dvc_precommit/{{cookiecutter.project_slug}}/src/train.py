"""
Model training script with production-ready features.

This module handles the complete model training workflow including:
- Configuration management
- Data loading and validation
- Model training with experiment tracking
- Model serialization and versioning
- Performance monitoring
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import hydra
import joblib
import numpy as np
import pandas as pd
from omegaconf import DictConfig, OmegaConf
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_validate, train_test_split

{% if cookiecutter.use_mlflow == 'yes' -%}
import mlflow
import mlflow.sklearn
{% endif -%}
{% if cookiecutter.use_wandb == 'yes' -%}
import wandb
{% endif -%}

from {{cookiecutter.project_slug}}.data.validation import validate_data
from {{cookiecutter.project_slug}}.features.build_features import FeatureEngineer
from {{cookiecutter.project_slug}}.models.model_factory import ModelFactory
from {{cookiecutter.project_slug}}.utils.logger import get_logger
from {{cookiecutter.project_slug}}.utils.metrics import calculate_metrics

# Configure structured logging
logger = get_logger(__name__)


class ModelTrainer:
    """Production-ready model trainer with MLOps best practices."""
    
    def __init__(self, config: DictConfig):
        """Initialize trainer with configuration."""
        self.config = config
        self.model = None
        self.feature_engineer = None
        self.metrics = {}
        
        # Set up paths
        self.data_dir = Path(config.paths.data_dir)
        self.model_dir = Path(config.paths.model_dir)
        self.reports_dir = Path(config.paths.reports_dir)
        
        # Create directories
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize experiment tracking
        self._init_experiment_tracking()
    
    def _init_experiment_tracking(self):
        """Initialize MLflow/WandB for experiment tracking."""
        {% if cookiecutter.use_mlflow == 'yes' -%}
        mlflow.set_tracking_uri(self.config.mlflow.tracking_uri)
        mlflow.set_experiment(self.config.mlflow.experiment_name)
        {% endif -%}
        
        {% if cookiecutter.use_wandb == 'yes' -%}
        wandb.init(
            project=self.config.wandb.project,
            config=OmegaConf.to_container(self.config, resolve=True),
            tags=self.config.wandb.tags,
        )
        {% endif -%}
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Load and validate training data."""
        logger.info("Loading training data")
        
        # Load features and targets
        features_path = self.data_dir / "features" / "train_features.parquet"
        targets_path = self.data_dir / "features" / "train_targets.parquet"
        
        if not features_path.exists() or not targets_path.exists():
            raise FileNotFoundError(
                f"Training data not found. Run feature engineering pipeline first."
            )
        
        X = pd.read_parquet(features_path)
        y = pd.read_parquet(targets_path).squeeze()
        
        # Validate data
        if self.config.training.validate_data:
            validation_results = validate_data(X, y, self.config.data.validation)
            if not validation_results["is_valid"]:
                raise ValueError(f"Data validation failed: {validation_results['errors']}")
        
        logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
        return X, y
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train model with cross-validation and hyperparameter tuning."""
        logger.info("Starting model training")
        
        # Initialize feature engineer
        self.feature_engineer = FeatureEngineer(self.config.features)
        X_transformed = self.feature_engineer.fit_transform(X)
        
        # Get model from factory
        model_factory = ModelFactory(self.config.model)
        self.model = model_factory.get_model()
        
        # Perform cross-validation
        cv_scores = cross_validate(
            self.model,
            X_transformed,
            y,
            cv=self.config.training.cv_folds,
            scoring=self.config.training.scoring_metrics,
            n_jobs=self.config.training.n_jobs,
            return_train_score=True,
        )
        
        # Log CV results
        for metric, scores in cv_scores.items():
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            logger.info(f"{metric}: {mean_score:.4f} (+/- {std_score:.4f})")
            self.metrics[f"cv_{metric}_mean"] = mean_score
            self.metrics[f"cv_{metric}_std"] = std_score
        
        # Train final model on full dataset
        self.model.fit(X_transformed, y)
        
        # Calculate training metrics
        train_pred = self.model.predict(X_transformed)
        train_metrics = calculate_metrics(y, train_pred, prefix="train")
        self.metrics.update(train_metrics)
        
        # Log metrics to experiment tracking
        self._log_metrics(self.metrics)
        
        logger.info("Model training completed")
    
    def save_model(self) -> None:
        """Save trained model and artifacts."""
        logger.info("Saving model artifacts")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_version = f"v_{timestamp}"
        
        # Save model
        model_path = self.model_dir / f"model_{model_version}.pkl"
        joblib.dump(self.model, model_path)
        
        # Save feature engineer
        fe_path = self.model_dir / f"feature_engineer_{model_version}.pkl"
        joblib.dump(self.feature_engineer, fe_path)
        
        # Save latest versions
        joblib.dump(self.model, self.model_dir / "model.pkl")
        joblib.dump(self.feature_engineer, self.model_dir / "feature_engineer.pkl")
        
        # Save model metadata
        metadata = {
            "version": model_version,
            "timestamp": timestamp,
            "config": OmegaConf.to_container(self.config, resolve=True),
            "metrics": self.metrics,
            "model_type": self.config.model.type,
            "feature_names": self.feature_engineer.get_feature_names(),
        }
        
        metadata_path = self.model_dir / f"metadata_{model_version}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Log model to experiment tracking
        {% if cookiecutter.use_mlflow == 'yes' -%}
        mlflow.sklearn.log_model(
            self.model,
            "model",
            registered_model_name=self.config.mlflow.model_name,
        )
        mlflow.log_artifact(str(fe_path), "feature_engineer")
        mlflow.log_artifact(str(metadata_path), "metadata")
        {% endif -%}
        
        logger.info(f"Model saved: {model_path}")
    
    def _log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log metrics to experiment tracking systems."""
        {% if cookiecutter.use_mlflow == 'yes' -%}
        mlflow.log_metrics(metrics)
        {% endif -%}
        
        {% if cookiecutter.use_wandb == 'yes' -%}
        wandb.log(metrics)
        {% endif -%}
        
        # Save metrics to file
        metrics_path = self.reports_dir / "training_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
    
    def run(self) -> None:
        """Execute complete training pipeline."""
        try:
            {% if cookiecutter.use_mlflow == 'yes' -%}
            with mlflow.start_run():
                # Log parameters
                mlflow.log_params(OmegaConf.to_container(self.config.model, resolve=True))
                mlflow.log_params(OmegaConf.to_container(self.config.training, resolve=True))
                
                # Training pipeline
                X, y = self.load_data()
                self.train(X, y)
                self.save_model()
            {% else -%}
            # Training pipeline
            X, y = self.load_data()
            self.train(X, y)
            self.save_model()
            {% endif -%}
            
            logger.info("Training pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}", exc_info=True)
            raise


@hydra.main(version_base=None, config_path="../config", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point for training."""
    logger.info("Starting training with config:")
    logger.info(OmegaConf.to_yaml(cfg))
    
    trainer = ModelTrainer(cfg)
    trainer.run()


if __name__ == "__main__":
    main()
