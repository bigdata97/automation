import csv
from google.cloud import spanner
from google.oauth2 import service_account

# === Configuration ===
csv_file_path = r"C:\path\to\your\file.csv"
project_id = "your-prod-project"
instance_id = "your-prod-instance"
database_id = "your-prod-database"
table_name = "your_table_name"
service_account_path = "resource_sa_prod.json"
chunk_size = 500  # rows per batch, safe limit

# === Connect to Spanner ===
def connect_to_spanner():
    credentials = service_account.Credentials.from_service_account_file(service_account_path)
    client = spanner.Client(project=project_id, credentials=credentials)
    instance = client.instance(instance_id)
    database = instance.database(database_id)
    return database

# === Read CSV in chunks ===
def read_csv_in_chunks(file_path, chunk_size):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        chunk = []
        for row in reader:
            chunk.append(row)
            if len(chunk) == chunk_size:
                yield headers, chunk
                chunk = []
        if chunk:
            yield headers, chunk

# === Insert chunk into Spanner ===
def insert_chunk(database, table_name, headers, rows):
    with database.batch() as batch:
        batch.insert(
            table=table_name,
            columns=headers,
            values=rows
        )
    print(f"✅ Inserted {len(rows)} rows")

# === Main Driver ===
def upload_csv_to_spanner():
    db = connect_to_spanner()
    total_inserted = 0

    for headers, chunk in read_csv_in_chunks(csv_file_path, chunk_size):
        insert_chunk(db, table_name, headers, chunk)
        total_inserted += len(chunk)

    print(f"🎉 All done. Total inserted rows: {total_inserted}")

if __name__ == "__main__":
    upload_csv_to_spanner()
