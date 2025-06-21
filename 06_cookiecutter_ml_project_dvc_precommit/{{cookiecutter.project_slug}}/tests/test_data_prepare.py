"""Tests for data preparation module."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.data.prepare import DataPreparer


class TestDataPreparer:
    """Test cases for DataPreparer class."""
    
    def test_initialization(self, config):
        """Test DataPreparer initialization."""
        preparer = DataPreparer(config)
        assert preparer.config == config
        assert preparer.prepare_config == config["prepare"]
        assert preparer.scaler is None
        assert preparer.imputer is None
    
    def test_handle_missing_values_drop(self, sample_data, config):
        """Test handling missing values with drop method."""
        config["prepare"]["handle_missing"] = "drop"
        preparer = DataPreparer(config)
        
        initial_len = len(sample_data)
        result = preparer.handle_missing_values(sample_data)
        
        # Should have fewer rows after dropping
        assert len(result) < initial_len
        assert result.isnull().sum().sum() == 0
    
    def test_handle_missing_values_impute(self, sample_data, config):
        """Test handling missing values with imputation."""
        config["prepare"]["handle_missing"] = "median"
        preparer = DataPreparer(config)
        
        result = preparer.handle_missing_values(sample_data)
        
        # Should have same number of rows
        assert len(result) == len(sample_data)
        # Should have no missing values
        assert result.isnull().sum().sum() == 0
        assert preparer.imputer is not None
    
    def test_remove_outliers_iqr(self, sample_data, config):
        """Test outlier removal using IQR method."""
        preparer = DataPreparer(config)
        
        # Add some extreme outliers
        sample_data.loc[0, "feature_1"] = 100
        sample_data.loc[1, "feature_2"] = -100
        
        initial_len = len(sample_data)
        result = preparer.remove_outliers(sample_data)
        
        # Should have fewer rows after removing outliers
        assert len(result) <= initial_len
        assert "removed_outliers" in str(preparer.metadata["transformations_applied"])
    
    def test_normalize_features(self, sample_data, config):
        """Test feature normalization."""
        preparer = DataPreparer(config)
        
        # Handle missing values first
        sample_data = preparer.handle_missing_values(sample_data)
        
        result = preparer.normalize_features(sample_data)
        
        # Check numeric columns are normalized
        numeric_cols = ["feature_1", "feature_2", "feature_4"]
        for col in numeric_cols:
            assert abs(result[col].mean()) < 0.1  # Close to 0
            assert 0.8 < result[col].std() < 1.2  # Close to 1
        
        assert preparer.scaler is not None
    
    def test_split_data(self, sample_data, config):
        """Test data splitting."""
        preparer = DataPreparer(config)
        
        train_df, val_df, test_df = preparer.split_data(sample_data)
        
        # Check split sizes
        total_len = len(sample_data)
        expected_test_size = int(total_len * 0.2)
        expected_val_size = int(total_len * 0.1)
        expected_train_size = total_len - expected_test_size - expected_val_size
        
        assert abs(len(test_df) - expected_test_size) <= 2
        assert abs(len(val_df) - expected_val_size) <= 2
        assert abs(len(train_df) - expected_train_size) <= 4
        
        # Check no overlap
        train_indices = set(train_df.index)
        val_indices = set(val_df.index)
        test_indices = set(test_df.index)
        
        assert len(train_indices & val_indices) == 0
        assert len(train_indices & test_indices) == 0
        assert len(val_indices & test_indices) == 0
    
    def test_prepare_pipeline(self, sample_data, config, temp_dir):
        """Test complete preparation pipeline."""
        preparer = DataPreparer(config)
        
        # Save sample data
        raw_dir = temp_dir / "raw"
        raw_dir.mkdir()
        sample_data.to_csv(raw_dir / "data.csv", index=False)
        
        # Run preparation
        output_dir = temp_dir / "processed"
        metadata = preparer.prepare(raw_dir, output_dir)
        
        # Check outputs exist
        assert (output_dir / "train.parquet").exists()
        assert (output_dir / "val.parquet").exists()
        assert (output_dir / "test.parquet").exists()
        assert (output_dir / "metadata.json").exists()
        
        # Check metadata
        assert metadata["original_shape"] == sample_data.shape
        assert "train_shape" in metadata
        assert "val_shape" in metadata
        assert "test_shape" in metadata
        
        # Load and verify processed data
        train_df = pd.read_parquet(output_dir / "train.parquet")
        assert train_df.isnull().sum().sum() == 0  # No missing values