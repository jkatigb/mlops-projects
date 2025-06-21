from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import tempfile
import json
import os


def prep_data(**context):
    """Prepare training data with mock operations for lineage."""
    print("Preparing data...")
    
    # Mock data preparation - creates lineage events
    data_dir = "/tmp/ml_pipeline"
    os.makedirs(data_dir, exist_ok=True)
    
    # Simulate reading raw data
    raw_data_path = f"{data_dir}/raw_data.csv"
    with open(raw_data_path, 'w') as f:
        f.write("id,feature1,feature2,label\n")
        f.write("1,0.1,0.2,0\n")
        f.write("2,0.3,0.4,1\n")
        f.write("3,0.5,0.6,1\n")
    print(f"Created raw dataset: {raw_data_path}")
    
    # Simulate data transformation
    processed_data_path = f"{data_dir}/processed_data.csv"
    with open(processed_data_path, 'w') as f:
        f.write("id,normalized_feature1,normalized_feature2,label\n")
        f.write("1,0.05,0.1,0\n")
        f.write("2,0.15,0.2,1\n")
        f.write("3,0.25,0.3,1\n")
    print(f"Created processed dataset: {processed_data_path}")
    
    # Push output path to XCom for downstream tasks
    context['task_instance'].xcom_push(key='processed_data_path', value=processed_data_path)
    return processed_data_path


def train_model(**context):
    """Train ML model with mock operations for lineage."""
    print("Training model...")
    
    # Get input data path from upstream task
    ti = context['task_instance']
    processed_data_path = ti.xcom_pull(task_ids='data_prep', key='processed_data_path')
    print(f"Reading training data from: {processed_data_path}")
    
    # Mock model training - creates lineage events
    model_dir = "/tmp/ml_pipeline/models"
    os.makedirs(model_dir, exist_ok=True)
    
    # Simulate model artifact
    model_path = f"{model_dir}/model_v{context['ds_nodash']}.pkl"
    with open(model_path, 'w') as f:
        model_metadata = {
            "model_type": "RandomForest",
            "accuracy": 0.95,
            "training_date": context['ds'],
            "version": context['ds_nodash'],
            "input_features": ["normalized_feature1", "normalized_feature2"],
            "training_data": processed_data_path
        }
        json.dump(model_metadata, f)
    print(f"Trained model saved: {model_path}")
    
    # Push model path to XCom
    ti.xcom_push(key='model_path', value=model_path)
    ti.xcom_push(key='model_version', value=f"v{context['ds_nodash']}")
    return model_path


def validate_model(**context):
    """Validate model performance."""
    print("Validating model...")
    
    # Get model path from upstream task
    ti = context['task_instance']
    model_path = ti.xcom_pull(task_ids='train_model', key='model_path')
    
    # Mock validation results
    validation_results = {
        "accuracy": 0.95,
        "precision": 0.94,
        "recall": 0.96,
        "f1_score": 0.95,
        "validation_date": context['ds'],
        "model_path": model_path
    }
    
    # Save validation results
    validation_path = f"/tmp/ml_pipeline/validation_results_{context['ds_nodash']}.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_results, f)
    
    print(f"Validation results: {validation_results}")
    ti.xcom_push(key='validation_passed', value=True)
    return validation_results


def deploy_model(**context):
    """Deploy model to serving infrastructure."""
    print("Deploying model...")
    
    # Get model information from upstream tasks
    ti = context['task_instance']
    model_path = ti.xcom_pull(task_ids='train_model', key='model_path')
    model_version = ti.xcom_pull(task_ids='train_model', key='model_version')
    validation_passed = ti.xcom_pull(task_ids='validate_model', key='validation_passed')
    
    if not validation_passed:
        raise ValueError("Model validation failed, skipping deployment")
    
    # Mock deployment metadata
    deployment_metadata = {
        "model_path": model_path,
        "model_version": model_version,
        "deployment_date": context['ds'],
        "deployment_type": "seldon-core",
        "endpoint": f"http://model-serving.example.com/v1/models/ml_model_{model_version}",
        "replicas": 3,
        "cpu_request": "500m",
        "memory_request": "1Gi"
    }
    
    # Save deployment info
    deployment_path = f"/tmp/ml_pipeline/deployment_{context['ds_nodash']}.json"
    with open(deployment_path, 'w') as f:
        json.dump(deployment_metadata, f)
    
    print(f"Model deployed: {deployment_metadata['endpoint']}")
    print(f"Deployment metadata saved: {deployment_path}")
    
    # In real implementation, we would:
    # - Build Docker image with model
    # - Push to registry
    # - Update Seldon/KServe deployment
    # - Run smoke tests
    
    return deployment_metadata


# Default arguments for all tasks
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': ['mlops@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    dag_id="ml_lineage",
    default_args=default_args,
    description='ML pipeline with OpenLineage tracking',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['ml', 'lineage', 'openlineage'],
)

with dag:
    # Task 1: Data preparation
    data_prep = PythonOperator(
        task_id="data_prep",
        python_callable=prep_data,
        provide_context=True,
        doc_md="""
        ### Data Preparation Task
        - Reads raw data from source
        - Performs data cleaning and normalization
        - Outputs processed dataset for training
        """
    )
    
    # Task 2: Model training
    train = PythonOperator(
        task_id="train_model",
        python_callable=train_model,
        provide_context=True,
        doc_md="""
        ### Model Training Task
        - Loads processed data from upstream task
        - Trains ML model (mock RandomForest)
        - Saves model artifact with metadata
        """
    )
    
    # Task 3: Model validation
    validate = PythonOperator(
        task_id="validate_model",
        python_callable=validate_model,
        provide_context=True,
        doc_md="""
        ### Model Validation Task
        - Loads trained model
        - Evaluates performance metrics
        - Determines if model meets deployment criteria
        """
    )
    
    # Task 4: Model deployment
    deploy = PythonOperator(
        task_id="deploy_model",
        python_callable=deploy_model,
        provide_context=True,
        doc_md="""
        ### Model Deployment Task
        - Deploys validated model to serving infrastructure
        - Updates model endpoint
        - Records deployment metadata
        """
    )
    
    # Optional: Clean up temporary files
    cleanup = BashOperator(
        task_id="cleanup",
        bash_command="find /tmp/ml_pipeline -type f -mtime +7 -delete || true",
        doc_md="Clean up old pipeline artifacts",
        trigger_rule="all_done"  # Run regardless of upstream success/failure
    )
    
    # Define task dependencies
    data_prep >> train >> validate >> deploy >> cleanup
