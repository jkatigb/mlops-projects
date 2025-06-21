"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_data():
    """Create sample dataset for testing."""
    np.random.seed(42)
    n_samples = 1000
    
    # Create features
    data = {
        "feature_1": np.random.normal(0, 1, n_samples),
        "feature_2": np.random.normal(5, 2, n_samples),
        "feature_3": np.random.choice(["A", "B", "C"], n_samples),
        "feature_4": np.random.uniform(0, 100, n_samples),
        "target": np.random.choice([0, 1], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Add some missing values
    mask = np.random.random(n_samples) < 0.1
    df.loc[mask, "feature_1"] = np.nan
    
    return df


@pytest.fixture
def config():
    """Create sample configuration."""
    return {
        "prepare": {
            "test_split": 0.2,
            "validation_split": 0.1,
            "seed": 42,
            "normalize": True,
            "handle_missing": "median",
            "outlier_method": "iqr",
            "outlier_threshold": 1.5
        },
        "features": {
            "engineering": {
                "polynomial_degree": 2,
                "interaction_only": False,
                "create_clusters": True,
                "n_clusters": 3,
                "encode_categorical": True,
                "encoding_method": "onehot"
            },
            "selection": {
                "method": "mutual_info",
                "k_best": 10,
                "variance_threshold": 0.01
            }
        },
        "model": {
            "type": "random_forest",
            "hyperparameters": {
                "n_estimators": 10,
                "max_depth": 5,
                "min_samples_split": 5,
                "min_samples_leaf": 2
            }
        },
        "training": {
            "batch_size": 32,
            "epochs": 10,
            "learning_rate": 0.001,
            "cross_validation": {
                "enabled": False,
                "n_splits": 3
            }
        },
        "evaluation": {
            "metrics": ["accuracy", "precision", "recall", "f1"],
            "bootstrap_iterations": 100,
            "confidence_level": 0.95
        }
    }


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    from sklearn.ensemble import RandomForestClassifier
    
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    
    # Fit on dummy data
    X = np.random.randn(100, 5)
    y = np.random.choice([0, 1], 100)
    model.fit(X, y)
    
    return model