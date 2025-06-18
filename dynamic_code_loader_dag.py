from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from google.cloud import storage
import importlib.util
import tempfile
import os

def execute_remote_script_from_gcs(bucket_name, object_name, **kwargs):
    # Step 1: Download Python file from GCS
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        blob.download_to_filename(temp_file.name)
        temp_file_path = temp_file.name

    # Step 2: Dynamically load the module
    module_name = os.path.splitext(os.path.basename(temp_file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, temp_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Step 3: Call the `run()` function
    if hasattr(module, "run"):
        return module.run(**kwargs)
    else:
        raise AttributeError("No function 'run' found in the module.")

with DAG(
    dag_id='dynamic_code_loader_dag',
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["dynamic", "gcs", "test"]
) as dag:

    dynamic_task = PythonOperator(
        task_id="run_hello_world_from_gcs",
        python_callable=execute_remote_script_from_gcs,
        op_kwargs={
            "bucket_name": "your-bucket",  # ← replace with your bucket
            "object_name": "code/hello_world.py"
        }
    )
