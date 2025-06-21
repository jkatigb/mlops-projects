#!/usr/bin/env python3
"""Model monitoring and drift detection for {{cookiecutter.project_name}}.

This module monitors model performance and detects data/concept drift.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error
import joblib
from datetime import datetime, timedelta

{% if cookiecutter.include_model_monitoring == 'yes' -%}
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset
from evidently.metrics import *
{% endif -%}

from ..utils.config import load_config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detects data drift and monitors model performance."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the drift detector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.monitoring_config = config.get("monitoring", {})
        self.drift_config = self.monitoring_config.get("drift_detection", {})
        self.performance_config = self.monitoring_config.get("performance", {})
        self.data_quality_config = self.monitoring_config.get("data_quality", {})
        
        self.model = None
        self.reference_data = None
        self.alerts = []
        self.metrics_history = []
    
    def load_model(self, model_path: Path) -> None:
        """Load trained model.
        
        Args:
            model_path: Path to model file
        """
        logger.info(f"Loading model from {model_path}")
        self.model = joblib.load(model_path)
    
    def load_reference_data(self, reference_path: Path) -> pd.DataFrame:
        """Load reference data for drift detection.
        
        Args:
            reference_path: Path to reference data
            
        Returns:
            Reference DataFrame
        """
        logger.info(f"Loading reference data from {reference_path}")
        self.reference_data = pd.read_parquet(reference_path)
        return self.reference_data
    
    def detect_feature_drift(
        self, reference_data: pd.DataFrame, current_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Detect drift in feature distributions.
        
        Args:
            reference_data: Reference dataset
            current_data: Current dataset
            
        Returns:
            Drift detection results
        """
        method = self.drift_config.get("method", "ks")
        threshold = self.drift_config.get("threshold", 0.1)
        
        drift_results = {
            "drifted_features": [],
            "drift_scores": {},
            "overall_drift": False
        }
        
        # Get numeric columns
        numeric_cols = reference_data.select_dtypes(include=[np.number]).columns
        if "target" in numeric_cols:
            numeric_cols = numeric_cols.drop("target")
        
        for col in numeric_cols:
            ref_values = reference_data[col].dropna()
            curr_values = current_data[col].dropna()
            
            if len(ref_values) == 0 or len(curr_values) == 0:
                continue
            
            # Calculate drift score based on method
            if method == "ks":
                # Kolmogorov-Smirnov test
                statistic, p_value = stats.ks_2samp(ref_values, curr_values)
                drift_score = statistic
            
            elif method == "chi2":
                # Chi-squared test for categorical data
                # Bin numeric data first
                n_bins = 10
                bins = np.histogram_bin_edges(
                    np.concatenate([ref_values, curr_values]), bins=n_bins
                )
                ref_hist, _ = np.histogram(ref_values, bins=bins)
                curr_hist, _ = np.histogram(curr_values, bins=bins)
                
                # Add small constant to avoid division by zero
                expected = (ref_hist + curr_hist) / 2 + 1e-10
                chi2_stat = np.sum((ref_hist - expected)**2 / expected)
                drift_score = chi2_stat / len(bins)
            
            elif method == "wasserstein":
                # Wasserstein distance
                drift_score = stats.wasserstein_distance(ref_values, curr_values)
            
            elif method == "psi":
                # Population Stability Index
                drift_score = self._calculate_psi(ref_values, curr_values)
            
            else:
                drift_score = 0
            
            drift_results["drift_scores"][col] = float(drift_score)
            
            # Check if drift detected
            if drift_score > threshold:
                drift_results["drifted_features"].append(col)
                logger.warning(f"Drift detected in feature '{col}': score={drift_score:.4f}")
        
        # Overall drift detection
        if len(drift_results["drifted_features"]) > 0:
            drift_results["overall_drift"] = True
            drift_percentage = len(drift_results["drifted_features"]) / len(numeric_cols)
            drift_results["drift_percentage"] = drift_percentage
            
            self.alerts.append({
                "type": "feature_drift",
                "severity": "high" if drift_percentage > 0.5 else "medium",
                "message": f"Feature drift detected in {len(drift_results['drifted_features'])} features",
                "timestamp": datetime.now().isoformat()
            })
        
        return drift_results
    
    def _calculate_psi(self, reference: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float:
        """Calculate Population Stability Index.
        
        Args:
            reference: Reference values
            current: Current values
            n_bins: Number of bins
            
        Returns:
            PSI value
        """
        # Create bins based on reference data
        _, bin_edges = np.histogram(reference, bins=n_bins)
        
        # Calculate frequencies
        ref_freq, _ = np.histogram(reference, bins=bin_edges)
        curr_freq, _ = np.histogram(current, bins=bin_edges)
        
        # Convert to proportions
        ref_prop = (ref_freq + 1) / (len(reference) + n_bins)  # Add 1 to avoid log(0)
        curr_prop = (curr_freq + 1) / (len(current) + n_bins)
        
        # Calculate PSI
        psi = np.sum((curr_prop - ref_prop) * np.log(curr_prop / ref_prop))
        
        return psi
    
    def monitor_model_performance(
        self, reference_data: pd.DataFrame, current_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Monitor model performance over time.
        
        Args:
            reference_data: Reference dataset with predictions
            current_data: Current dataset
            
        Returns:
            Performance monitoring results
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Separate features and target
        X_ref = reference_data.drop(columns=["target"])
        y_ref = reference_data["target"]
        X_curr = current_data.drop(columns=["target"])
        y_curr = current_data["target"]
        
        # Make predictions
        y_ref_pred = self.model.predict(X_ref)
        y_curr_pred = self.model.predict(X_curr)
        
        # Calculate metrics
        performance_results = {}
        
        if hasattr(self.model, "predict_proba"):
            # Classification metrics
            ref_accuracy = accuracy_score(y_ref, y_ref_pred)
            curr_accuracy = accuracy_score(y_curr, y_curr_pred)
            ref_f1 = f1_score(y_ref, y_ref_pred, average="weighted")
            curr_f1 = f1_score(y_curr, y_curr_pred, average="weighted")
            
            performance_results["reference_metrics"] = {
                "accuracy": float(ref_accuracy),
                "f1_score": float(ref_f1)
            }
            performance_results["current_metrics"] = {
                "accuracy": float(curr_accuracy),
                "f1_score": float(curr_f1)
            }
            
            # Calculate degradation
            accuracy_drop = ref_accuracy - curr_accuracy
            f1_drop = ref_f1 - curr_f1
            
            performance_results["performance_drop"] = {
                "accuracy": float(accuracy_drop),
                "f1_score": float(f1_drop)
            }
            
            # Check for alerts
            alert_threshold = self.performance_config.get("alert_threshold", 0.05)
            if accuracy_drop > alert_threshold:
                self.alerts.append({
                    "type": "performance_degradation",
                    "severity": "high",
                    "message": f"Model accuracy dropped by {accuracy_drop:.2%}",
                    "timestamp": datetime.now().isoformat()
                })
        else:
            # Regression metrics
            ref_mse = mean_squared_error(y_ref, y_ref_pred)
            curr_mse = mean_squared_error(y_curr, y_curr_pred)
            
            performance_results["reference_metrics"] = {"mse": float(ref_mse)}
            performance_results["current_metrics"] = {"mse": float(curr_mse)}
            
            # Calculate degradation
            mse_increase = (curr_mse - ref_mse) / ref_mse
            performance_results["performance_drop"] = {"mse_increase": float(mse_increase)}
            
            # Check for alerts
            if mse_increase > 0.1:  # 10% increase
                self.alerts.append({
                    "type": "performance_degradation",
                    "severity": "high",
                    "message": f"Model MSE increased by {mse_increase:.2%}",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Store in history
        self.metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "metrics": performance_results["current_metrics"]
        })
        
        return performance_results
    
    def check_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Check data quality issues.
        
        Args:
            data: Dataset to check
            
        Returns:
            Data quality results
        """
        quality_results = {
            "missing_values": {},
            "anomalies": {},
            "quality_score": 1.0,
            "issues": []
        }
        
        # Check missing values
        if self.data_quality_config.get("check_missing", True):
            for col in data.columns:
                missing_ratio = data[col].isnull().sum() / len(data)
                if missing_ratio > 0:
                    quality_results["missing_values"][col] = float(missing_ratio)
                    
                    if missing_ratio > 0.1:  # More than 10% missing
                        quality_results["issues"].append({
                            "type": "high_missing_values",
                            "column": col,
                            "missing_ratio": float(missing_ratio)
                        })
        
        # Check value ranges
        if self.data_quality_config.get("check_range", True):
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                # Check for extreme values (beyond 5 standard deviations)
                mean_val = data[col].mean()
                std_val = data[col].std()
                
                if std_val > 0:
                    z_scores = np.abs((data[col] - mean_val) / std_val)
                    extreme_values = (z_scores > 5).sum()
                    
                    if extreme_values > 0:
                        quality_results["anomalies"][col] = int(extreme_values)
                        quality_results["issues"].append({
                            "type": "extreme_values",
                            "column": col,
                            "count": int(extreme_values)
                        })
        
        # Check uniqueness
        if self.data_quality_config.get("check_uniqueness", True):
            for col in data.columns:
                if "id" in col.lower():
                    duplicates = data[col].duplicated().sum()
                    if duplicates > 0:
                        quality_results["issues"].append({
                            "type": "duplicate_ids",
                            "column": col,
                            "count": int(duplicates)
                        })
        
        # Calculate overall quality score
        total_issues = len(quality_results["issues"])
        quality_results["quality_score"] = max(0, 1 - (total_issues * 0.1))
        
        # Add alerts for severe issues
        if quality_results["quality_score"] < 0.8:
            self.alerts.append({
                "type": "data_quality",
                "severity": "medium",
                "message": f"Data quality score: {quality_results['quality_score']:.2f}",
                "timestamp": datetime.now().isoformat()
            })
        
        return quality_results
    
    {% if cookiecutter.include_model_monitoring == 'yes' -%}
    def generate_evidently_report(
        self, reference_data: pd.DataFrame, current_data: pd.DataFrame,
        output_path: Path
    ) -> None:
        """Generate comprehensive monitoring report using Evidently.
        
        Args:
            reference_data: Reference dataset
            current_data: Current dataset
            output_path: Path to save report
        """
        logger.info("Generating Evidently monitoring report...")
        
        # Create column mapping
        column_mapping = ColumnMapping()
        column_mapping.target = "target"
        column_mapping.prediction = "prediction" if "prediction" in reference_data.columns else None
        column_mapping.numerical_features = reference_data.select_dtypes(
            include=[np.number]
        ).columns.drop("target", errors="ignore").tolist()
        
        # Create drift report
        drift_report = Report(metrics=[
            DataDriftPreset(),
            TargetDriftPreset(),
            DataQualityPreset()
        ])
        
        drift_report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping
        )
        
        # Save report
        drift_report_path = output_path / "drift_report.html"
        drift_report.save_html(str(drift_report_path))
        logger.info(f"Saved drift report to {drift_report_path}")
        
        # Create performance report if predictions available
        if "prediction" in reference_data.columns:
            performance_report = Report(metrics=[
                ClassificationQualityMetric() if hasattr(self.model, "predict_proba") 
                else RegressionQualityMetric(),
                ClassificationQualityByClass() if hasattr(self.model, "predict_proba")
                else None
            ])
            
            performance_report.run(
                reference_data=reference_data,
                current_data=current_data,
                column_mapping=column_mapping
            )
            
            performance_report_path = output_path / "performance_report.html"
            performance_report.save_html(str(performance_report_path))
            logger.info(f"Saved performance report to {performance_report_path}")
    {% endif -%}
    
    def monitor(
        self, reference_path: Path, monitoring_data_path: Path,
        output_path: Path
    ) -> Dict[str, Any]:
        """Run complete monitoring pipeline.
        
        Args:
            reference_path: Path to reference data
            monitoring_data_path: Path to current monitoring data
            output_path: Path to save monitoring reports
            
        Returns:
            Monitoring results
        """
        # Load data
        reference_data = self.load_reference_data(reference_path)
        
        # Find monitoring data files
        monitoring_files = sorted(monitoring_data_path.glob("*.parquet"))
        
        if not monitoring_files:
            logger.warning(f"No monitoring data found in {monitoring_data_path}")
            return {"status": "no_data"}
        
        # Process latest monitoring data
        latest_file = monitoring_files[-1]
        logger.info(f"Processing monitoring data from {latest_file}")
        current_data = pd.read_parquet(latest_file)
        
        # Run monitoring checks
        results = {
            "timestamp": datetime.now().isoformat(),
            "data_file": str(latest_file),
            "alerts": []
        }
        
        # Feature drift detection
        logger.info("Detecting feature drift...")
        drift_results = self.detect_feature_drift(reference_data, current_data)
        results["drift_detection"] = drift_results
        
        # Performance monitoring
        if self.model:
            logger.info("Monitoring model performance...")
            performance_results = self.monitor_model_performance(reference_data, current_data)
            results["performance_monitoring"] = performance_results
        
        # Data quality checks
        logger.info("Checking data quality...")
        quality_results = self.check_data_quality(current_data)
        results["data_quality"] = quality_results
        
        # Add all alerts
        results["alerts"] = self.alerts
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        {% if cookiecutter.include_model_monitoring == 'yes' -%}
        # Generate Evidently reports
        self.generate_evidently_report(reference_data, current_data, output_path)
        {% endif -%}
        
        # Save monitoring metrics
        metrics_path = output_path / "drift_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved monitoring metrics to {metrics_path}")
        
        # Log alerts
        if self.alerts:
            logger.warning(f"Generated {len(self.alerts)} monitoring alerts:")
            for alert in self.alerts:
                logger.warning(f"  - [{alert['severity']}] {alert['message']}")
        
        return results


def main():
    """Main monitoring function."""
    parser = argparse.ArgumentParser(description="Monitor model and detect drift")
    parser.add_argument("--config", type=Path, required=True, help="Configuration file path")
    parser.add_argument("--model-path", type=Path, help="Path to trained model")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize drift detector
    detector = DriftDetector(config)
    
    # Load model if provided
    if args.model_path:
        detector.load_model(args.model_path)
    
    # Run monitoring
    results = detector.monitor(
        Path("data/features/train.parquet"),
        Path("data/monitoring"),
        Path("reports/monitoring")
    )
    
    if results.get("alerts"):
        logger.warning("Monitoring completed with alerts!")
        exit(1)  # Exit with error code if alerts generated
    else:
        logger.info("Monitoring completed successfully - no issues detected")


if __name__ == "__main__":
    main()