#!/usr/bin/env python3
"""Model evaluation module for {{cookiecutter.project_name}}.

This module performs comprehensive model evaluation and generates reports.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc,
    precision_recall_curve, mean_squared_error, mean_absolute_error,
    r2_score, explained_variance_score
)
import joblib
from datetime import datetime

{% if cookiecutter.use_mlflow == 'yes' -%}
import mlflow
{% endif -%}

{% if cookiecutter.use_wandb == 'yes' -%}
import wandb
{% endif -%}

from ..utils.config import load_config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluates trained models and generates comprehensive reports."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the model evaluator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.evaluation_config = config.get("evaluation", {})
        self.model = None
        self.results = {
            "metrics": {},
            "plots": {},
            "analysis": {},
            "metadata": {
                "evaluation_date": datetime.now().isoformat(),
                "config": config
            }
        }
    
    def load_model(self, model_path: Path) -> Any:
        """Load trained model from disk.
        
        Args:
            model_path: Path to model file
            
        Returns:
            Loaded model
        """
        logger.info(f"Loading model from {model_path}")
        self.model = joblib.load(model_path)
        return self.model
    
    def evaluate_classification(
        self, y_true: np.ndarray, y_pred: np.ndarray, y_proba: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Evaluate classification model.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Prediction probabilities (optional)
            
        Returns:
            Dictionary of evaluation metrics
        """
        metrics = {}
        
        # Basic metrics
        metrics["accuracy"] = accuracy_score(y_true, y_pred)
        metrics["precision"] = precision_score(y_true, y_pred, average="weighted")
        metrics["recall"] = recall_score(y_true, y_pred, average="weighted")
        metrics["f1"] = f1_score(y_true, y_pred, average="weighted")
        
        # Per-class metrics
        report = classification_report(y_true, y_pred, output_dict=True)
        metrics["classification_report"] = report
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics["confusion_matrix"] = cm.tolist()
        
        # ROC-AUC if probabilities available
        if y_proba is not None and len(np.unique(y_true)) == 2:
            # Binary classification
            fpr, tpr, _ = roc_curve(y_true, y_proba[:, 1])
            metrics["auc_roc"] = auc(fpr, tpr)
            metrics["roc_curve"] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
            
            # Precision-Recall curve
            precision, recall, _ = precision_recall_curve(y_true, y_proba[:, 1])
            metrics["auc_pr"] = auc(recall, precision)
            metrics["pr_curve"] = {"precision": precision.tolist(), "recall": recall.tolist()}
        
        return metrics
    
    def evaluate_regression(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """Evaluate regression model.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dictionary of evaluation metrics
        """
        metrics = {}
        
        # Basic metrics
        metrics["mse"] = mean_squared_error(y_true, y_pred)
        metrics["rmse"] = np.sqrt(metrics["mse"])
        metrics["mae"] = mean_absolute_error(y_true, y_pred)
        metrics["r2"] = r2_score(y_true, y_pred)
        metrics["explained_variance"] = explained_variance_score(y_true, y_pred)
        
        # Additional analysis
        residuals = y_true - y_pred
        metrics["residual_mean"] = float(np.mean(residuals))
        metrics["residual_std"] = float(np.std(residuals))
        
        # Percentile errors
        abs_errors = np.abs(residuals)
        metrics["median_absolute_error"] = float(np.median(abs_errors))
        metrics["percentile_90_error"] = float(np.percentile(abs_errors, 90))
        metrics["percentile_95_error"] = float(np.percentile(abs_errors, 95))
        
        return metrics
    
    def plot_confusion_matrix(self, cm: np.ndarray, class_names: List[str], save_path: Path) -> None:
        """Plot confusion matrix.
        
        Args:
            cm: Confusion matrix
            class_names: List of class names
            save_path: Path to save the plot
        """
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=class_names, yticklabels=class_names
        )
        plt.title("Confusion Matrix")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        
        logger.info(f"Saved confusion matrix plot to {save_path}")
    
    def plot_roc_curve(self, fpr: np.ndarray, tpr: np.ndarray, auc_score: float, save_path: Path) -> None:
        """Plot ROC curve.
        
        Args:
            fpr: False positive rates
            tpr: True positive rates
            auc_score: AUC score
            save_path: Path to save the plot
        """
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {auc_score:.2f})")
        plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("Receiver Operating Characteristic")
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        
        logger.info(f"Saved ROC curve plot to {save_path}")
    
    def plot_residuals(self, y_true: np.ndarray, y_pred: np.ndarray, save_path: Path) -> None:
        """Plot residuals for regression.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            save_path: Path to save the plot
        """
        residuals = y_true - y_pred
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Residuals vs Predicted
        axes[0, 0].scatter(y_pred, residuals, alpha=0.5)
        axes[0, 0].axhline(y=0, color="r", linestyle="--")
        axes[0, 0].set_xlabel("Predicted Values")
        axes[0, 0].set_ylabel("Residuals")
        axes[0, 0].set_title("Residuals vs Predicted")
        
        # Histogram of residuals
        axes[0, 1].hist(residuals, bins=30, edgecolor="black")
        axes[0, 1].set_xlabel("Residuals")
        axes[0, 1].set_ylabel("Frequency")
        axes[0, 1].set_title("Distribution of Residuals")
        
        # Q-Q plot
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1, 0])
        axes[1, 0].set_title("Q-Q Plot")
        
        # True vs Predicted
        axes[1, 1].scatter(y_true, y_pred, alpha=0.5)
        axes[1, 1].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], "r--", lw=2)
        axes[1, 1].set_xlabel("True Values")
        axes[1, 1].set_ylabel("Predicted Values")
        axes[1, 1].set_title("True vs Predicted")
        
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        
        logger.info(f"Saved residual plots to {save_path}")
    
    def perform_bootstrap_evaluation(
        self, X: pd.DataFrame, y: pd.Series, n_iterations: int = 1000
    ) -> Dict[str, Any]:
        """Perform bootstrap evaluation for confidence intervals.
        
        Args:
            X: Features
            y: Target
            n_iterations: Number of bootstrap iterations
            
        Returns:
            Dictionary with confidence intervals
        """
        logger.info(f"Performing bootstrap evaluation with {n_iterations} iterations")
        
        metrics_list = []
        n_samples = len(X)
        
        for i in range(n_iterations):
            # Bootstrap sample
            indices = np.random.choice(n_samples, n_samples, replace=True)
            X_boot = X.iloc[indices]
            y_boot = y.iloc[indices]
            
            # Make predictions
            y_pred = self.model.predict(X_boot)
            
            # Calculate metrics
            if self._is_classification():
                metrics_list.append({
                    "accuracy": accuracy_score(y_boot, y_pred),
                    "f1": f1_score(y_boot, y_pred, average="weighted")
                })
            else:
                metrics_list.append({
                    "rmse": np.sqrt(mean_squared_error(y_boot, y_pred)),
                    "r2": r2_score(y_boot, y_pred)
                })
        
        # Calculate confidence intervals
        metrics_df = pd.DataFrame(metrics_list)
        confidence_level = self.evaluation_config.get("confidence_level", 0.95)
        alpha = 1 - confidence_level
        
        results = {}
        for metric in metrics_df.columns:
            values = metrics_df[metric].values
            lower = np.percentile(values, alpha/2 * 100)
            upper = np.percentile(values, (1 - alpha/2) * 100)
            results[metric] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "lower": float(lower),
                "upper": float(upper)
            }
        
        return results
    
    def _is_classification(self) -> bool:
        """Determine if this is a classification task."""
        # Check if model has predict_proba method
        return hasattr(self.model, "predict_proba")
    
    def evaluate(self, model_path: Path, test_data_path: Path) -> Dict[str, Any]:
        """Run complete evaluation pipeline.
        
        Args:
            model_path: Path to trained model
            test_data_path: Path to test data
            
        Returns:
            Evaluation results
        """
        # Load model
        self.load_model(model_path / "model.pkl")
        
        # Load test data
        logger.info("Loading test data...")
        X_test = pd.read_parquet(test_data_path)
        y_test = X_test["target"]
        X_test = X_test.drop(columns=["target"])
        
        logger.info(f"Test data shape: {X_test.shape}")
        
        # Make predictions
        y_pred = self.model.predict(X_test)
        
        # Get probabilities for classification
        y_proba = None
        if self._is_classification() and hasattr(self.model, "predict_proba"):
            y_proba = self.model.predict_proba(X_test)
        
        # Evaluate model
        if self._is_classification():
            metrics = self.evaluate_classification(y_test, y_pred, y_proba)
            
            # Create plots directory
            plots_dir = Path("reports/figures")
            plots_dir.mkdir(parents=True, exist_ok=True)
            
            # Plot confusion matrix
            if "confusion_matrix" in metrics:
                cm = np.array(metrics["confusion_matrix"])
                class_names = [str(i) for i in range(cm.shape[0])]
                self.plot_confusion_matrix(cm, class_names, plots_dir / "confusion_matrix.png")
            
            # Plot ROC curve
            if "roc_curve" in metrics:
                fpr = np.array(metrics["roc_curve"]["fpr"])
                tpr = np.array(metrics["roc_curve"]["tpr"])
                self.plot_roc_curve(fpr, tpr, metrics["auc_roc"], plots_dir / "roc_curve.png")
        else:
            metrics = self.evaluate_regression(y_test, y_pred)
            
            # Create plots directory
            plots_dir = Path("reports/figures")
            plots_dir.mkdir(parents=True, exist_ok=True)
            
            # Plot residuals
            self.plot_residuals(y_test.values, y_pred, plots_dir / "residual_plots.png")
        
        # Perform bootstrap evaluation if enabled
        if self.evaluation_config.get("bootstrap_iterations", 0) > 0:
            bootstrap_results = self.perform_bootstrap_evaluation(
                X_test, y_test,
                n_iterations=self.evaluation_config["bootstrap_iterations"]
            )
            metrics["bootstrap_confidence_intervals"] = bootstrap_results
        
        # Update results
        self.results["metrics"] = metrics
        self.results["test_size"] = len(X_test)
        
        # Save metrics
        metrics_file = Path("reports/evaluation_metrics.json")
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(v) for v in obj]
            return obj
        
        serializable_results = convert_numpy(self.results)
        
        with open(metrics_file, "w") as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Saved evaluation metrics to {metrics_file}")
        
        {% if cookiecutter.use_mlflow == 'yes' -%}
        # Log to MLflow
        with mlflow.start_run():
            mlflow.log_metrics(
                {k: v for k, v in metrics.items() 
                 if isinstance(v, (int, float))}
            )
            mlflow.log_artifacts("reports/figures")
        {% endif -%}
        
        {% if cookiecutter.use_wandb == 'yes' -%}
        # Log to Weights & Biases
        wandb.log(
            {k: v for k, v in metrics.items() 
             if isinstance(v, (int, float))}
        )
        
        # Log plots
        for plot_file in plots_dir.glob("*.png"):
            wandb.log({plot_file.stem: wandb.Image(str(plot_file))})
        {% endif -%}
        
        return self.results


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument("--config", type=Path, required=True, help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Evaluate model
    evaluator = ModelEvaluator(config)
    results = evaluator.evaluate(
        Path("models"),
        Path("data/features/test.parquet")
    )
    
    logger.info("Model evaluation completed successfully!")
    
    # Print key metrics
    metrics = results["metrics"]
    if "accuracy" in metrics:
        logger.info(f"Test Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"Test F1 Score: {metrics['f1']:.4f}")
    else:
        logger.info(f"Test RMSE: {metrics['rmse']:.4f}")
        logger.info(f"Test R²: {metrics['r2']:.4f}")


if __name__ == "__main__":
    main()