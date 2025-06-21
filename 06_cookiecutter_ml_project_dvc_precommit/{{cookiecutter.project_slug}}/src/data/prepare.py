#!/usr/bin/env python3
"""Data preparation module for {{cookiecutter.project_name}}.

This module handles data cleaning, splitting, and preprocessing.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedShuffleSplit
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer
import joblib

from ..utils.config import load_config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class DataPreparer:
    """Prepares data for machine learning pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the data preparer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.prepare_config = config.get("prepare", {})
        self.scaler = None
        self.imputer = None
        self.metadata = {
            "original_shape": None,
            "processed_shape": None,
            "columns_removed": [],
            "transformations_applied": []
        }
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values according to configuration.
        
        Args:
            df: DataFrame with potential missing values
            
        Returns:
            DataFrame with missing values handled
        """
        method = self.prepare_config.get("handle_missing", "median")
        logger.info(f"Handling missing values using method: {method}")
        
        if method == "drop":
            # Drop rows with any missing values
            df_clean = df.dropna()
            rows_dropped = len(df) - len(df_clean)
            if rows_dropped > 0:
                logger.info(f"Dropped {rows_dropped} rows with missing values")
            self.metadata["transformations_applied"].append(f"dropped_missing_rows: {rows_dropped}")
            return df_clean
        
        # Separate numeric and categorical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        
        # Handle numeric columns
        if numeric_cols:
            if method == "knn":
                imputer = KNNImputer(n_neighbors=5)
                df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
            else:
                # Use SimpleImputer for mean/median/mode
                strategy = method if method in ["mean", "median"] else "median"
                imputer = SimpleImputer(strategy=strategy)
                df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
            
            self.imputer = imputer  # Save for later use
        
        # Handle categorical columns
        if categorical_cols:
            # Use mode for categorical columns
            mode_imputer = SimpleImputer(strategy="most_frequent")
            df[categorical_cols] = mode_imputer.fit_transform(df[categorical_cols])
        
        self.metadata["transformations_applied"].append(f"imputed_missing_values: {method}")
        return df
    
    def remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove outliers from numerical columns.
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with outliers removed
        """
        method = self.prepare_config.get("outlier_method", "iqr")
        threshold = self.prepare_config.get("outlier_threshold", 1.5)
        
        if method == "none":
            return df
        
        logger.info(f"Removing outliers using method: {method}")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Skip target column if present
        if "target" in numeric_cols:
            numeric_cols.remove("target")
        
        initial_rows = len(df)
        mask = pd.Series([True] * len(df))
        
        for col in numeric_cols:
            if method == "iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                col_mask = ~((df[col] < (Q1 - threshold * IQR)) | 
                            (df[col] > (Q3 + threshold * IQR)))
            elif method == "zscore":
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                col_mask = z_scores <= threshold
            else:
                col_mask = pd.Series([True] * len(df))
            
            mask = mask & col_mask
        
        df_clean = df[mask]
        rows_removed = initial_rows - len(df_clean)
        
        if rows_removed > 0:
            logger.info(f"Removed {rows_removed} rows containing outliers")
            self.metadata["transformations_applied"].append(f"removed_outliers: {rows_removed}")
        
        return df_clean
    
    def normalize_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize numerical features.
        
        Args:
            df: DataFrame to normalize
            
        Returns:
            Normalized DataFrame
        """
        if not self.prepare_config.get("normalize", True):
            return df
        
        logger.info("Normalizing numerical features")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Skip target column if present
        if "target" in numeric_cols:
            numeric_cols.remove("target")
        
        if numeric_cols:
            # Choose scaler based on outlier handling
            if self.prepare_config.get("outlier_method", "iqr") == "none":
                self.scaler = RobustScaler()  # More robust to outliers
            else:
                self.scaler = StandardScaler()  # Standard normalization
            
            df[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
            self.metadata["transformations_applied"].append("normalized_features")
        
        return df
    
    def split_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split data into train, validation, and test sets.
        
        Args:
            df: DataFrame to split
            
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        test_size = self.prepare_config.get("test_split", 0.2)
        val_size = self.prepare_config.get("validation_split", 0.1)
        seed = self.prepare_config.get("seed", 42)
        
        logger.info(f"Splitting data - test: {test_size}, val: {val_size}")
        
        # First split: train+val vs test
        if "target" in df.columns:
            # Stratified split for classification
            try:
                train_val_df, test_df = train_test_split(
                    df, test_size=test_size, random_state=seed, stratify=df["target"]
                )
            except:
                # Fall back to regular split if stratification fails
                train_val_df, test_df = train_test_split(
                    df, test_size=test_size, random_state=seed
                )
        else:
            train_val_df, test_df = train_test_split(
                df, test_size=test_size, random_state=seed
            )
        
        # Second split: train vs val
        val_size_adjusted = val_size / (1 - test_size)  # Adjust for the remaining data
        
        if "target" in df.columns:
            try:
                train_df, val_df = train_test_split(
                    train_val_df, test_size=val_size_adjusted, random_state=seed,
                    stratify=train_val_df["target"]
                )
            except:
                train_df, val_df = train_test_split(
                    train_val_df, test_size=val_size_adjusted, random_state=seed
                )
        else:
            train_df, val_df = train_test_split(
                train_val_df, test_size=val_size_adjusted, random_state=seed
            )
        
        logger.info(f"Data split - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        
        return train_df, val_df, test_df
    
    def prepare(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Run complete data preparation pipeline.
        
        Args:
            input_path: Path to raw data directory
            output_path: Path to save processed data
            
        Returns:
            Preparation metadata
        """
        # Find data files
        data_files = list(input_path.glob("*.csv")) + list(input_path.glob("*.parquet"))
        
        if not data_files:
            raise ValueError(f"No data files found in {input_path}")
        
        # Load data
        logger.info(f"Loading data from {data_files[0]}")
        if data_files[0].suffix == ".csv":
            df = pd.read_csv(data_files[0])
        else:
            df = pd.read_parquet(data_files[0])
        
        self.metadata["original_shape"] = df.shape
        logger.info(f"Loaded data shape: {df.shape}")
        
        # Handle missing values
        df = self.handle_missing_values(df)
        
        # Remove outliers
        df = self.remove_outliers(df)
        
        # Normalize features
        df = self.normalize_features(df)
        
        # Split data
        train_df, val_df, test_df = self.split_data(df)
        
        # Save processed data
        output_path.mkdir(parents=True, exist_ok=True)
        
        train_path = output_path / "train.parquet"
        val_path = output_path / "val.parquet"
        test_path = output_path / "test.parquet"
        
        train_df.to_parquet(train_path, index=False)
        val_df.to_parquet(val_path, index=False)
        test_df.to_parquet(test_path, index=False)
        
        logger.info(f"Saved processed data to {output_path}")
        
        # Save preprocessing artifacts
        if self.scaler:
            joblib.dump(self.scaler, output_path / "scaler.pkl")
        if self.imputer:
            joblib.dump(self.imputer, output_path / "imputer.pkl")
        
        # Update metadata
        self.metadata["processed_shape"] = df.shape
        self.metadata["train_shape"] = train_df.shape
        self.metadata["val_shape"] = val_df.shape
        self.metadata["test_shape"] = test_df.shape
        
        # Save metadata
        with open(output_path / "metadata.json", "w") as f:
            json.dump(self.metadata, f, indent=2)
        
        return self.metadata


def main():
    """Main preparation function."""
    parser = argparse.ArgumentParser(description="Prepare data for training")
    parser.add_argument("--config", type=Path, required=True, help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Prepare data
    preparer = DataPreparer(config)
    metadata = preparer.prepare(
        Path("data/raw"),
        Path("data/processed")
    )
    
    logger.info("Data preparation completed successfully!")


if __name__ == "__main__":
    main()