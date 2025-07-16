import csv
from google.cloud import spanner
from google.cloud import storage

PROJECT_ID = 'your-project-id'
INSTANCE_ID = 'your-instance-id'
DATABASE_ID = 'source-db-id'
TABLE_NAME = 'cc_work_all_tables'
BUCKET_NAME = 'your-gcs-bucket-name'
GCS_BLOB_NAME = 'spanner_exports/cc_work_all_tables.csv'
LOCAL_CSV_FILE = '/tmp/cc_work_all_tables.csv'

def connect_spanner(project_id, instance_id, database_id):
    client = spanner.Client(project=project_id)
    instance = client.instance(instance_id)
    database = instance.database(database_id)
    return database

def upload_to_gcs(bucket_name, source_file, destination_blob):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    print(f"Uploaded to gs://{bucket_name}/{destination_blob}")

def export_spanner_to_csv():
    db = connect_spanner(PROJECT_ID, INSTANCE_ID, DATABASE_ID)

    with open(LOCAL_CSV_FILE, 'w', newline='') as csvfile:
        with db.snapshot() as snapshot:
            results = snapshot.execute_sql(f"SELECT * FROM {TABLE_NAME}")
            field_names = [field.name for field in results.metadata.row_type.fields]

            writer = csv.writer(csvfile)
            writer.writerow(field_names)
            for row in results:
                writer.writerow(list(row))

    print(f"Exported data to local file: {LOCAL_CSV_FILE}")
    upload_to_gcs(BUCKET_NAME, LOCAL_CSV_FILE, GCS_BLOB_NAME)

if __name__ == "__main__":
    export_spanner_to_csv()











import csv
import os
from google.cloud import storage
from google.cloud import spanner

PROJECT_ID = 'your-project-id'
INSTANCE_ID = 'your-instance-id'
DATABASE_ID = 'destination-db-id'
TABLE_NAME = 'cc_work_all_tables'
BUCKET_NAME = 'your-gcs-bucket-name'
GCS_BLOB_NAME = 'spanner_exports/cc_work_all_tables.csv'
LOCAL_CSV_FILE = '/tmp/cc_work_all_tables.csv'
CHUNK_SIZE = 500

def connect_spanner(project_id, instance_id, database_id):
    client = spanner.Client(project=project_id)
    instance = client.instance(instance_id)
    database = instance.database(database_id)
    return database

def download_from_gcs(bucket_name, blob_name, destination_file):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(destination_file)
    print(f"Downloaded file from gs://{bucket_name}/{blob_name} to {destination_file}")

def chunk_data(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def insert_into_spanner(database, table_name, columns, rows):
    with database.batch() as batch:
        batch.insert(
            table=table_name,
            columns=columns,
            values=rows
        )
    print(f"Inserted {len(rows)} rows")

def import_csv_to_spanner():
    db = connect_spanner(PROJECT_ID, INSTANCE_ID, DATABASE_ID)
    download_from_gcs(BUCKET_NAME, GCS_BLOB_NAME, LOCAL_CSV_FILE)

    with open(LOCAL_CSV_FILE, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)
        headers = rows[0]
        data_rows = rows[1:]

    for chunk in chunk_data(data_rows, CHUNK_SIZE):
        insert_into_spanner(db, TABLE_NAME, headers, chunk)

if __name__ == "__main__":
    import_csv_to_spanner()
