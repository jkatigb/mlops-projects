#!/usr/bin/env python3
"""Feature engineering module for {{cookiecutter.project_name}}.

This module handles feature creation, transformation, and selection.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures, OneHotEncoder, LabelEncoder, TargetEncoder
from sklearn.feature_selection import (
    SelectKBest, mutual_info_classif, mutual_info_regression,
    chi2, f_classif, f_regression, VarianceThreshold, RFE
)
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.decomposition import PCA
import joblib

from ..utils.config import load_config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Creates and selects features for machine learning."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the feature engineer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.features_config = config.get("features", {})
        self.engineering_config = self.features_config.get("engineering", {})
        self.selection_config = self.features_config.get("selection", {})
        
        self.encoders = {}
        self.feature_selector = None
        self.polynomial_transformer = None
        self.clustering_model = None
        self.selected_features = []
        
        self.metadata = {
            "original_features": [],
            "engineered_features": [],
            "selected_features": [],
            "feature_importance": {},
            "transformations_applied": []
        }
    
    def create_polynomial_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create polynomial and interaction features.
        
        Args:
            df: DataFrame with numerical features
            
        Returns:
            DataFrame with polynomial features added
        """
        degree = self.engineering_config.get("polynomial_degree", 2)
        interaction_only = self.engineering_config.get("interaction_only", False)
        
        if degree <= 1:
            return df
        
        logger.info(f"Creating polynomial features (degree={degree})")
        
        # Select only numerical features
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Exclude target if present
        if "target" in numeric_cols:
            numeric_cols.remove("target")
            target_col = df["target"]
        else:
            target_col = None
        
        if not numeric_cols:
            return df
        
        # Create polynomial features
        self.polynomial_transformer = PolynomialFeatures(
            degree=degree,
            interaction_only=interaction_only,
            include_bias=False
        )
        
        poly_features = self.polynomial_transformer.fit_transform(df[numeric_cols])
        feature_names = self.polynomial_transformer.get_feature_names_out(numeric_cols)
        
        # Create new dataframe with polynomial features
        poly_df = pd.DataFrame(poly_features, columns=feature_names, index=df.index)
        
        # Combine with non-numeric features
        non_numeric_cols = [col for col in df.columns if col not in numeric_cols and col != "target"]
        result_df = pd.concat([poly_df, df[non_numeric_cols]], axis=1)
        
        # Add back target if it existed
        if target_col is not None:
            result_df["target"] = target_col
        
        self.metadata["transformations_applied"].append(f"polynomial_features_degree_{degree}")
        logger.info(f"Created {len(feature_names) - len(numeric_cols)} new polynomial features")
        
        return result_df
    
    def create_cluster_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create cluster-based features.
        
        Args:
            df: DataFrame with features
            
        Returns:
            DataFrame with cluster features added
        """
        if not self.engineering_config.get("create_clusters", True):
            return df
        
        n_clusters = self.engineering_config.get("n_clusters", 5)
        logger.info(f"Creating cluster features (n_clusters={n_clusters})")
        
        # Select numerical features for clustering
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Exclude target if present
        if "target" in numeric_cols:
            numeric_cols.remove("target")
        
        if len(numeric_cols) < 2:
            logger.warning("Not enough numerical features for clustering")
            return df
        
        # Fit clustering model
        self.clustering_model = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = self.clustering_model.fit_predict(df[numeric_cols])
        
        # Add cluster labels as new feature
        df["cluster"] = cluster_labels
        
        # Add distance to each cluster center
        distances = self.clustering_model.transform(df[numeric_cols])
        for i in range(n_clusters):
            df[f"distance_to_cluster_{i}"] = distances[:, i]
        
        self.metadata["transformations_applied"].append(f"cluster_features_n_{n_clusters}")
        logger.info(f"Created {n_clusters + 1} cluster-based features")
        
        return df
    
    def encode_categorical_features(self, df: pd.DataFrame, is_train: bool = True) -> pd.DataFrame:
        """Encode categorical features.
        
        Args:
            df: DataFrame with categorical features
            is_train: Whether this is training data (fit encoders)
            
        Returns:
            DataFrame with encoded features
        """
        if not self.engineering_config.get("encode_categorical", True):
            return df
        
        method = self.engineering_config.get("encoding_method", "target")
        logger.info(f"Encoding categorical features using method: {method}")
        
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        
        # Exclude target if present
        if "target" in categorical_cols:
            categorical_cols.remove("target")
        
        if not categorical_cols:
            return df
        
        # Store target for target encoding
        target = df.get("target") if "target" in df.columns else None
        
        for col in categorical_cols:
            if method == "onehot":
                # One-hot encoding
                if is_train:
                    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
                    encoded = encoder.fit_transform(df[[col]])
                    self.encoders[col] = encoder
                else:
                    encoded = self.encoders[col].transform(df[[col]])
                
                # Create column names
                feature_names = [f"{col}_{cat}" for cat in encoder.categories_[0]]
                encoded_df = pd.DataFrame(encoded, columns=feature_names, index=df.index)
                
                # Drop original column and add encoded columns
                df = df.drop(columns=[col])
                df = pd.concat([df, encoded_df], axis=1)
                
            elif method == "label":
                # Label encoding
                if is_train:
                    encoder = LabelEncoder()
                    df[col] = encoder.fit_transform(df[col])
                    self.encoders[col] = encoder
                else:
                    # Handle unknown categories
                    df[col] = df[col].map(
                        lambda x: self.encoders[col].transform([x])[0] 
                        if x in self.encoders[col].classes_ else -1
                    )
            
            elif method == "target" and target is not None:
                # Target encoding (mean encoding)
                if is_train:
                    # Calculate mean target value for each category
                    encoding_map = df.groupby(col)["target"].mean().to_dict()
                    self.encoders[col] = encoding_map
                    df[col] = df[col].map(encoding_map)
                else:
                    # Use global mean for unknown categories
                    global_mean = np.mean(list(self.encoders[col].values()))
                    df[col] = df[col].map(lambda x: self.encoders[col].get(x, global_mean))
        
        self.metadata["transformations_applied"].append(f"categorical_encoding_{method}")
        return df
    
    def select_features(self, df: pd.DataFrame, is_train: bool = True) -> pd.DataFrame:
        """Select best features based on importance.
        
        Args:
            df: DataFrame with all features
            is_train: Whether this is training data (fit selector)
            
        Returns:
            DataFrame with selected features
        """
        method = self.selection_config.get("method", "mutual_info")
        k_best = self.selection_config.get("k_best", 20)
        variance_threshold = self.selection_config.get("variance_threshold", 0.01)
        
        if method == "none":
            return df
        
        logger.info(f"Selecting features using method: {method}")
        
        # Separate features and target
        if "target" in df.columns:
            X = df.drop(columns=["target"])
            y = df["target"]
        else:
            logger.warning("No target column found for feature selection")
            return df
        
        # First, remove low variance features
        if variance_threshold > 0 and is_train:
            var_selector = VarianceThreshold(threshold=variance_threshold)
            var_selector.fit(X)
            low_var_features = X.columns[~var_selector.get_support()].tolist()
            if low_var_features:
                logger.info(f"Removing {len(low_var_features)} low variance features")
                X = X.drop(columns=low_var_features)
                self.metadata["transformations_applied"].append(
                    f"removed_low_variance_{len(low_var_features)}"
                )
        
        # Select k best features
        if method == "mutual_info":
            # Determine if regression or classification
            if y.dtype in [np.float32, np.float64] and len(np.unique(y)) > 10:
                selector = SelectKBest(mutual_info_regression, k=min(k_best, X.shape[1]))
            else:
                selector = SelectKBest(mutual_info_classif, k=min(k_best, X.shape[1]))
        
        elif method == "chi2":
            # Chi2 only works with non-negative features
            if (X >= 0).all().all():
                selector = SelectKBest(chi2, k=min(k_best, X.shape[1]))
            else:
                logger.warning("Chi2 requires non-negative features, falling back to f_classif")
                selector = SelectKBest(f_classif, k=min(k_best, X.shape[1]))
        
        elif method == "anova":
            if y.dtype in [np.float32, np.float64] and len(np.unique(y)) > 10:
                selector = SelectKBest(f_regression, k=min(k_best, X.shape[1]))
            else:
                selector = SelectKBest(f_classif, k=min(k_best, X.shape[1]))
        
        elif method == "recursive":
            # Use Random Forest for RFE
            if y.dtype in [np.float32, np.float64] and len(np.unique(y)) > 10:
                estimator = RandomForestRegressor(n_estimators=50, random_state=42)
            else:
                estimator = RandomForestClassifier(n_estimators=50, random_state=42)
            selector = RFE(estimator, n_features_to_select=min(k_best, X.shape[1]))
        
        else:
            logger.warning(f"Unknown selection method: {method}")
            return df
        
        if is_train:
            # Fit selector
            selector.fit(X, y)
            self.feature_selector = selector
            
            # Get selected features
            if hasattr(selector, "scores_"):
                # For SelectKBest
                feature_scores = pd.Series(selector.scores_, index=X.columns)
                self.selected_features = feature_scores.nlargest(min(k_best, X.shape[1])).index.tolist()
                self.metadata["feature_importance"] = feature_scores.to_dict()
            else:
                # For RFE
                self.selected_features = X.columns[selector.support_].tolist()
                if hasattr(selector.estimator_, "feature_importances_"):
                    self.metadata["feature_importance"] = dict(
                        zip(X.columns, selector.estimator_.feature_importances_)
                    )
        
        # Apply selection
        X_selected = X[self.selected_features]
        
        # Add target back
        result_df = X_selected.copy()
        result_df["target"] = y
        
        logger.info(f"Selected {len(self.selected_features)} features from {X.shape[1]}")
        self.metadata["transformations_applied"].append(f"feature_selection_{method}_k{k_best}")
        self.metadata["selected_features"] = self.selected_features
        
        return result_df
    
    def build_features(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Run complete feature engineering pipeline.
        
        Args:
            input_path: Path to processed data directory
            output_path: Path to save feature data
            
        Returns:
            Feature engineering metadata
        """
        # Load processed data
        train_df = pd.read_parquet(input_path / "train.parquet")
        val_df = pd.read_parquet(input_path / "val.parquet")
        test_df = pd.read_parquet(input_path / "test.parquet")
        
        self.metadata["original_features"] = train_df.columns.tolist()
        logger.info(f"Loaded data - Train: {train_df.shape}, Val: {val_df.shape}, Test: {test_df.shape}")
        
        # Apply feature engineering to train data
        logger.info("Engineering features for training data...")
        train_df = self.create_polynomial_features(train_df)
        train_df = self.create_cluster_features(train_df)
        train_df = self.encode_categorical_features(train_df, is_train=True)
        train_df = self.select_features(train_df, is_train=True)
        
        # Apply same transformations to validation and test data
        logger.info("Applying transformations to validation data...")
        val_df = self.create_polynomial_features(val_df)
        if self.clustering_model:
            numeric_cols = val_df.select_dtypes(include=[np.number]).columns.tolist()
            if "target" in numeric_cols:
                numeric_cols.remove("target")
            
            cluster_labels = self.clustering_model.predict(val_df[numeric_cols[:len(numeric_cols)]])
            val_df["cluster"] = cluster_labels
            
            distances = self.clustering_model.transform(val_df[numeric_cols[:len(numeric_cols)]])
            for i in range(self.clustering_model.n_clusters):
                val_df[f"distance_to_cluster_{i}"] = distances[:, i]
        
        val_df = self.encode_categorical_features(val_df, is_train=False)
        if "target" in val_df.columns:
            target = val_df["target"]
            val_df = val_df[self.selected_features]
            val_df["target"] = target
        
        logger.info("Applying transformations to test data...")
        test_df = self.create_polynomial_features(test_df)
        if self.clustering_model:
            numeric_cols = test_df.select_dtypes(include=[np.number]).columns.tolist()
            if "target" in numeric_cols:
                numeric_cols.remove("target")
            
            cluster_labels = self.clustering_model.predict(test_df[numeric_cols[:len(numeric_cols)]])
            test_df["cluster"] = cluster_labels
            
            distances = self.clustering_model.transform(test_df[numeric_cols[:len(numeric_cols)]])
            for i in range(self.clustering_model.n_clusters):
                test_df[f"distance_to_cluster_{i}"] = distances[:, i]
        
        test_df = self.encode_categorical_features(test_df, is_train=False)
        if "target" in test_df.columns:
            target = test_df["target"]
            test_df = test_df[self.selected_features]
            test_df["target"] = target
        
        # Save feature data
        output_path.mkdir(parents=True, exist_ok=True)
        
        train_df.to_parquet(output_path / "train.parquet", index=False)
        val_df.to_parquet(output_path / "val.parquet", index=False)
        test_df.to_parquet(output_path / "test.parquet", index=False)
        
        # Save feature engineering artifacts
        artifacts = {
            "encoders": self.encoders,
            "feature_selector": self.feature_selector,
            "polynomial_transformer": self.polynomial_transformer,
            "clustering_model": self.clustering_model,
            "selected_features": self.selected_features
        }
        
        joblib.dump(artifacts, output_path / "feature_artifacts.pkl")
        
        # Update metadata
        self.metadata["engineered_features"] = train_df.columns.tolist()
        self.metadata["final_shape"] = {
            "train": train_df.shape,
            "val": val_df.shape,
            "test": test_df.shape
        }
        
        # Save metadata
        with open(output_path / "feature_metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)
        
        logger.info(f"Saved engineered features to {output_path}")
        
        return self.metadata


def main():
    """Main feature engineering function."""
    parser = argparse.ArgumentParser(description="Build features for training")
    parser.add_argument("--config", type=Path, required=True, help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Build features
    engineer = FeatureEngineer(config)
    metadata = engineer.build_features(
        Path("data/processed"),
        Path("data/features")
    )
    
    logger.info("Feature engineering completed successfully!")


if __name__ == "__main__":
    main()