#!/usr/bin/env python3
"""Model export module for {{cookiecutter.project_name}}.

This module handles exporting trained models to various formats.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd
import onnx
import onnxruntime as ort
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

from ..utils.config import load_config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class ModelExporter:
    """Exports trained models to various formats."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the model exporter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.export_config = config.get("export", {})
        self.model = None
        self.preprocessor = None
        self.feature_artifacts = None
    
    def load_artifacts(self, model_path: Path) -> None:
        """Load model and associated artifacts.
        
        Args:
            model_path: Path to model directory
        """
        logger.info("Loading model artifacts...")
        
        # Load model
        self.model = joblib.load(model_path / "model.pkl")
        
        # Load preprocessor if exists
        preprocessor_path = model_path / "preprocessor.pkl"
        if preprocessor_path.exists():
            self.preprocessor = joblib.load(preprocessor_path)
            logger.info("Loaded preprocessor")
        
        # Load feature artifacts if exist
        feature_artifacts_path = model_path / "feature_artifacts.pkl"
        if feature_artifacts_path.exists():
            self.feature_artifacts = joblib.load(feature_artifacts_path)
            logger.info("Loaded feature artifacts")
    
    def export_to_onnx(self, output_path: Path, sample_data: Optional[pd.DataFrame] = None) -> Path:
        """Export model to ONNX format.
        
        Args:
            output_path: Path to save ONNX model
            sample_data: Sample data for shape inference
            
        Returns:
            Path to exported model
        """
        logger.info("Exporting model to ONNX format...")
        
        # Determine input shape
        if sample_data is not None:
            n_features = sample_data.shape[1]
        elif hasattr(self.model, "n_features_in_"):
            n_features = self.model.n_features_in_
        else:
            # Try to infer from feature artifacts
            if self.feature_artifacts and "selected_features" in self.feature_artifacts:
                n_features = len(self.feature_artifacts["selected_features"])
            else:
                raise ValueError("Cannot determine input shape for ONNX export")
        
        # Define input type
        initial_type = [("float_input", FloatTensorType([None, n_features]))]
        
        # Convert to ONNX
        try:
            onnx_model = convert_sklearn(
                self.model,
                initial_types=initial_type,
                target_opset=12
            )
            
            # Save ONNX model
            onnx_path = output_path / "model.onnx"
            onnx_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(onnx_path, "wb") as f:
                f.write(onnx_model.SerializeToString())
            
            # Verify the model
            onnx.checker.check_model(onnx_model)
            logger.info(f"ONNX model saved to {onnx_path}")
            
            # Test inference if sample data provided
            if sample_data is not None:
                self._test_onnx_inference(onnx_path, sample_data)
            
            return onnx_path
            
        except Exception as e:
            logger.error(f"Failed to export to ONNX: {e}")
            raise
    
    def _test_onnx_inference(self, onnx_path: Path, sample_data: pd.DataFrame) -> None:
        """Test ONNX model inference.
        
        Args:
            onnx_path: Path to ONNX model
            sample_data: Sample data for testing
        """
        logger.info("Testing ONNX inference...")
        
        # Create inference session
        sess = ort.InferenceSession(str(onnx_path))
        
        # Get input name
        input_name = sess.get_inputs()[0].name
        
        # Prepare input data
        input_data = sample_data.values.astype(np.float32)
        
        # Run inference
        result = sess.run(None, {input_name: input_data})
        
        # Compare with sklearn predictions
        sklearn_pred = self.model.predict(sample_data)
        onnx_pred = result[0]
        
        # Check if predictions match (within tolerance)
        if hasattr(self.model, "predict_proba"):
            # Classification - compare class predictions
            onnx_pred_classes = np.argmax(onnx_pred, axis=1)
            matches = np.allclose(sklearn_pred, onnx_pred_classes)
        else:
            # Regression - compare values
            matches = np.allclose(sklearn_pred, onnx_pred.ravel(), rtol=1e-5)
        
        if matches:
            logger.info("ONNX inference test passed!")
        else:
            logger.warning("ONNX predictions don't match sklearn predictions exactly")
    
    def export_to_pickle(self, output_path: Path) -> Path:
        """Export model to optimized pickle format.
        
        Args:
            output_path: Path to save pickle model
            
        Returns:
            Path to exported model
        """
        logger.info("Exporting model to pickle format...")
        
        pickle_path = output_path / "model_optimized.pkl"
        pickle_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with compression
        joblib.dump(self.model, pickle_path, compress=3)
        
        logger.info(f"Pickle model saved to {pickle_path}")
        return pickle_path
    
    def create_model_metadata(self) -> Dict[str, Any]:
        """Create comprehensive model metadata.
        
        Returns:
            Model metadata dictionary
        """
        metadata = {
            "version": self.export_config.get("metadata", {}).get("version", "1.0.0"),
            "author": self.export_config.get("metadata", {}).get("author", "Unknown"),
            "description": self.export_config.get("metadata", {}).get("description", ""),
            "model_type": self.config.get("model", {}).get("type", "unknown"),
            "export_format": self.export_config.get("format", "onnx"),
            "export_date": pd.Timestamp.now().isoformat(),
            "model_info": {}
        }
        
        # Add model-specific information
        if hasattr(self.model, "feature_importances_"):
            metadata["model_info"]["feature_importances"] = dict(
                zip(
                    self.feature_artifacts.get("selected_features", []),
                    self.model.feature_importances_.tolist()
                )
            )
        
        if hasattr(self.model, "n_features_in_"):
            metadata["model_info"]["n_features"] = self.model.n_features_in_
        
        if hasattr(self.model, "classes_"):
            metadata["model_info"]["classes"] = self.model.classes_.tolist()
        
        # Add preprocessing information
        if self.preprocessor:
            metadata["preprocessing"] = {
                "scaler_type": type(self.preprocessor).__name__,
                "fitted": True
            }
        
        # Add feature engineering information
        if self.feature_artifacts:
            metadata["feature_engineering"] = {
                "selected_features": self.feature_artifacts.get("selected_features", []),
                "n_selected_features": len(self.feature_artifacts.get("selected_features", [])),
                "transformations": []
            }
            
            if self.feature_artifacts.get("polynomial_transformer"):
                metadata["feature_engineering"]["transformations"].append("polynomial")
            
            if self.feature_artifacts.get("clustering_model"):
                metadata["feature_engineering"]["transformations"].append("clustering")
        
        return metadata
    
    def create_inference_pipeline(self, output_path: Path) -> None:
        """Create a complete inference pipeline with preprocessing.
        
        Args:
            output_path: Path to save pipeline artifacts
        """
        logger.info("Creating inference pipeline...")
        
        pipeline_path = output_path / "inference_pipeline"
        pipeline_path.mkdir(parents=True, exist_ok=True)
        
        # Save all components
        components = {
            "model": self.model,
            "preprocessor": self.preprocessor,
            "feature_artifacts": self.feature_artifacts
        }
        
        for name, component in components.items():
            if component is not None:
                joblib.dump(component, pipeline_path / f"{name}.pkl")
        
        # Create inference script
        inference_script = '''#!/usr/bin/env python3
"""Inference script for {{cookiecutter.project_name}}."""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path


class ModelInference:
    """Handles model inference with preprocessing."""
    
    def __init__(self, pipeline_path: Path):
        """Load inference pipeline components."""
        self.model = joblib.load(pipeline_path / "model.pkl")
        
        # Load optional components
        preprocessor_path = pipeline_path / "preprocessor.pkl"
        if preprocessor_path.exists():
            self.preprocessor = joblib.load(preprocessor_path)
        else:
            self.preprocessor = None
        
        feature_artifacts_path = pipeline_path / "feature_artifacts.pkl"
        if feature_artifacts_path.exists():
            self.feature_artifacts = joblib.load(feature_artifacts_path)
        else:
            self.feature_artifacts = None
    
    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply preprocessing to input data."""
        # Apply scaling if available
        if self.preprocessor:
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            data[numeric_cols] = self.preprocessor.transform(data[numeric_cols])
        
        # Select features if available
        if self.feature_artifacts and "selected_features" in self.feature_artifacts:
            features = self.feature_artifacts["selected_features"]
            data = data[features]
        
        return data
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Make predictions on input data."""
        # Preprocess
        data = self.preprocess(data)
        
        # Predict
        predictions = self.model.predict(data)
        
        return predictions
    
    def predict_proba(self, data: pd.DataFrame) -> np.ndarray:
        """Get prediction probabilities for classification."""
        if not hasattr(self.model, "predict_proba"):
            raise ValueError("Model does not support probability predictions")
        
        # Preprocess
        data = self.preprocess(data)
        
        # Predict probabilities
        probabilities = self.model.predict_proba(data)
        
        return probabilities


if __name__ == "__main__":
    # Example usage
    inference = ModelInference(Path(__file__).parent)
    
    # Load your data
    # data = pd.read_csv("input.csv")
    # predictions = inference.predict(data)
    # print(predictions)
'''
        
        with open(pipeline_path / "inference.py", "w") as f:
            f.write(inference_script)
        
        logger.info(f"Inference pipeline saved to {pipeline_path}")
    
    def export(self, model_path: Path, output_path: Path) -> Dict[str, Any]:
        """Run complete export pipeline.
        
        Args:
            model_path: Path to trained model directory
            output_path: Path to save exported models
            
        Returns:
            Export metadata
        """
        # Load artifacts
        self.load_artifacts(model_path)
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        export_results = {}
        
        # Export based on format
        export_format = self.export_config.get("format", "onnx")
        
        if export_format == "onnx":
            # Load sample data for shape inference
            sample_data_path = Path("data/features/train.parquet")
            if sample_data_path.exists():
                sample_data = pd.read_parquet(sample_data_path).head(10)
                if "target" in sample_data.columns:
                    sample_data = sample_data.drop(columns=["target"])
            else:
                sample_data = None
            
            try:
                onnx_path = self.export_to_onnx(output_path, sample_data)
                export_results["onnx_path"] = str(onnx_path)
                export_results["export_success"] = True
            except Exception as e:
                logger.error(f"ONNX export failed: {e}")
                export_results["export_success"] = False
                export_results["error"] = str(e)
        
        elif export_format == "pickle":
            pickle_path = self.export_to_pickle(output_path)
            export_results["pickle_path"] = str(pickle_path)
            export_results["export_success"] = True
        
        else:
            logger.warning(f"Unsupported export format: {export_format}")
            export_results["export_success"] = False
            export_results["error"] = f"Unsupported format: {export_format}"
        
        # Always create inference pipeline if requested
        if self.export_config.get("include_preprocessing", True):
            self.create_inference_pipeline(output_path)
            export_results["inference_pipeline"] = str(output_path / "inference_pipeline")
        
        # Create and save metadata
        metadata = self.create_model_metadata()
        metadata["export_results"] = export_results
        
        with open(output_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Export completed. Results saved to {output_path}")
        
        return metadata


def main():
    """Main export function."""
    parser = argparse.ArgumentParser(description="Export trained model")
    parser.add_argument("--config", type=Path, required=True, help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Export model
    exporter = ModelExporter(config)
    metadata = exporter.export(
        Path("models"),
        Path("models/exported")
    )
    
    logger.info("Model export completed successfully!")
    if metadata.get("export_results", {}).get("export_success"):
        logger.info(f"Model exported to: {metadata.get('export_results')}")


if __name__ == "__main__":
    main()