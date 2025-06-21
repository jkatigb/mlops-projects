#!/usr/bin/env python3
"""Data validation module for {{cookiecutter.project_name}}.

This module performs comprehensive data quality checks and generates
validation reports for the input data.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from pandas_profiling import ProfileReport
import great_expectations as ge
from great_expectations.dataset.pandas_dataset import PandasDataset

from ..utils.config import load_config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates data quality and generates comprehensive reports."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the data validator.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path) if config_path else {}
        self.validation_results = {}
        self.metrics = {
            "total_records": 0,
            "total_features": 0,
            "missing_values": {},
            "data_types": {},
            "unique_counts": {},
            "validation_passed": True,
            "validation_errors": []
        }
    
    def validate_schema(self, df: pd.DataFrame, expected_schema: Dict[str, str]) -> List[str]:
        """Validate dataframe schema against expected schema.
        
        Args:
            df: DataFrame to validate
            expected_schema: Expected column names and types
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for missing columns
        missing_cols = set(expected_schema.keys()) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        
        # Check data types
        for col, expected_type in expected_schema.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if not self._compatible_types(actual_type, expected_type):
                    errors.append(
                        f"Column '{col}' has type '{actual_type}', "
                        f"expected '{expected_type}'"
                    )
        
        return errors
    
    def _compatible_types(self, actual: str, expected: str) -> bool:
        """Check if actual and expected types are compatible."""
        type_mappings = {
            "int": ["int64", "int32", "int16", "int8"],
            "float": ["float64", "float32", "float16"],
            "string": ["object", "string"],
            "datetime": ["datetime64[ns]", "datetime64"]
        }
        
        for expected_type, compatible_types in type_mappings.items():
            if expected in expected_type and any(t in actual for t in compatible_types):
                return True
        
        return actual == expected
    
    def check_missing_values(self, df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, float]:
        """Check for missing values in the dataframe.
        
        Args:
            df: DataFrame to check
            threshold: Maximum allowed missing value ratio
            
        Returns:
            Dictionary of columns with missing value ratios
        """
        missing_ratios = {}
        
        for col in df.columns:
            missing_ratio = df[col].isnull().sum() / len(df)
            if missing_ratio > 0:
                missing_ratios[col] = missing_ratio
                
                if missing_ratio > threshold:
                    self.metrics["validation_errors"].append(
                        f"Column '{col}' has {missing_ratio:.2%} missing values "
                        f"(exceeds threshold of {threshold:.2%})"
                    )
        
        return missing_ratios
    
    def check_duplicates(self, df: pd.DataFrame) -> Tuple[int, pd.DataFrame]:
        """Check for duplicate records.
        
        Args:
            df: DataFrame to check
            
        Returns:
            Tuple of (duplicate count, duplicate records)
        """
        duplicates = df[df.duplicated()]
        duplicate_count = len(duplicates)
        
        if duplicate_count > 0:
            self.metrics["validation_errors"].append(
                f"Found {duplicate_count} duplicate records"
            )
        
        return duplicate_count, duplicates
    
    def check_outliers(self, df: pd.DataFrame, method: str = "iqr", threshold: float = 1.5) -> Dict[str, int]:
        """Check for outliers in numerical columns.
        
        Args:
            df: DataFrame to check
            method: Outlier detection method ('iqr', 'zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Dictionary of columns with outlier counts
        """
        outlier_counts = {}
        
        for col in df.select_dtypes(include=[np.number]).columns:
            if method == "iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((df[col] < (Q1 - threshold * IQR)) | 
                           (df[col] > (Q3 + threshold * IQR))).sum()
            elif method == "zscore":
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outliers = (z_scores > threshold).sum()
            else:
                outliers = 0
            
            if outliers > 0:
                outlier_counts[col] = int(outliers)
        
        return outlier_counts
    
    def validate_expectations(self, df: pd.DataFrame, expectations_path: Optional[Path] = None) -> Dict[str, Any]:
        """Validate data against Great Expectations suite.
        
        Args:
            df: DataFrame to validate
            expectations_path: Path to expectations JSON file
            
        Returns:
            Validation results
        """
        ge_df = ge.from_pandas(df)
        results = {"success": True, "results": []}
        
        # Basic expectations
        for col in df.columns:
            # Check for nulls
            result = ge_df.expect_column_values_to_not_be_null(col)
            results["results"].append(result)
            if not result["success"]:
                results["success"] = False
            
            # Check for unique values if ID column
            if "id" in col.lower():
                result = ge_df.expect_column_values_to_be_unique(col)
                results["results"].append(result)
                if not result["success"]:
                    results["success"] = False
        
        # Load custom expectations if provided
        if expectations_path and expectations_path.exists():
            with open(expectations_path) as f:
                custom_expectations = json.load(f)
                # Apply custom expectations here
        
        return results
    
    def generate_profile_report(self, df: pd.DataFrame, output_path: Path) -> None:
        """Generate comprehensive data profiling report.
        
        Args:
            df: DataFrame to profile
            output_path: Path to save the HTML report
        """
        profile = ProfileReport(
            df,
            title=f"Data Validation Report - {{cookiecutter.project_name}}",
            explorative=True,
            dark_mode=False,
            minimal=False,
            samples={"head": 20, "tail": 20},
            correlations={
                "pearson": {"calculate": True},
                "spearman": {"calculate": True},
                "kendall": {"calculate": False},
                "phi_k": {"calculate": False},
                "cramers": {"calculate": False}
            }
        )
        
        profile.to_file(output_path)
        logger.info(f"Generated profile report: {output_path}")
    
    def validate(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Run complete validation pipeline.
        
        Args:
            input_path: Path to input data directory
            output_path: Path to save validation report
            
        Returns:
            Validation metrics
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
        
        # Update basic metrics
        self.metrics["total_records"] = len(df)
        self.metrics["total_features"] = len(df.columns)
        self.metrics["data_types"] = df.dtypes.astype(str).to_dict()
        
        # Run validation checks
        logger.info("Running validation checks...")
        
        # Check missing values
        self.metrics["missing_values"] = self.check_missing_values(df)
        
        # Check duplicates
        duplicate_count, _ = self.check_duplicates(df)
        self.metrics["duplicate_count"] = duplicate_count
        
        # Check outliers
        self.metrics["outlier_counts"] = self.check_outliers(df)
        
        # Check unique values
        for col in df.columns:
            self.metrics["unique_counts"][col] = df[col].nunique()
        
        # Generate profile report
        logger.info("Generating profile report...")
        self.generate_profile_report(df, output_path)
        
        # Determine overall validation status
        self.metrics["validation_passed"] = len(self.metrics["validation_errors"]) == 0
        
        return self.metrics


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate input data")
    parser.add_argument("--input", type=Path, required=True, help="Input data directory")
    parser.add_argument("--output", type=Path, required=True, help="Output report path")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Create output directory
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Run validation
    validator = DataValidator(args.config)
    metrics = validator.validate(args.input, args.output)
    
    # Save metrics
    metrics_path = args.output.parent / "data_validation_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved validation metrics to {metrics_path}")
    
    # Exit with error if validation failed
    if not metrics["validation_passed"]:
        logger.error("Data validation failed!")
        for error in metrics["validation_errors"]:
            logger.error(f"  - {error}")
        exit(1)
    else:
        logger.info("Data validation passed!")


if __name__ == "__main__":
    main()