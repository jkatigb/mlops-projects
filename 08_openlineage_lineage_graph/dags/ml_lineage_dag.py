from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def prep_data():
    print("Preparing data...")


def train_model():
    print("Training model...")


def deploy_model():
    # In real life we'd call Seldon/KServe APIs
    print("Deploying model via Seldon/KServe...")


definition = DAG(
    dag_id="ml_lineage",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
)

with definition:
    data_prep = PythonOperator(task_id="data_prep", python_callable=prep_data)
    train = PythonOperator(task_id="train_model", python_callable=train_model)
    deploy = PythonOperator(task_id="deploy_model", python_callable=deploy_model)

    data_prep >> train >> deploy
