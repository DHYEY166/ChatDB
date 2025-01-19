import mysql.connector
from pymongo import MongoClient, ASCENDING
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from typing import Dict, Any, List


def connect_to_sql(connection_string: str):
    """
    Establish a connection to a MySQL database using the provided connection string.
    """
    try:
        import re
        # Parse the connection string
        pattern = r"mysql\+mysqlconnector://(?P<username>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<database>.+)"
        match = re.match(pattern, connection_string)
        if not match:
            raise ValueError("Invalid connection string format")

        # Extract parameters
        params = match.groupdict()

        # Establish connection
        conn = mysql.connector.connect(
            user=params["username"],
            password=params["password"],
            host=params["host"],
            port=int(params["port"]),
            database=params["database"]
        )
        return conn
    except mysql.connector.Error as err:
        raise Exception(f"Error connecting to MySQL: {err}")


class DatabaseImporter:
    @staticmethod
    def create_mysql_database(host: str, user: str, password: str, database_name: str) -> bool:
        """
        Create a MySQL database.
        """
        try:
            conn = mysql.connector.connect(host=host, user=user, password=password)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
            conn.close()
            print(f"Database '{database_name}' created successfully.")
            return True
        except Exception as e:
            print(f"Error creating MySQL database: {e}")
            return False

    @staticmethod
    def import_csv_to_mysql(host: str, user: str, password: str, database_name: str, file_path: str, table_name: str) -> bool:
        """
        Import a CSV file into a MySQL table.
        """
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            conn = mysql.connector.connect(host=host, user=user, password=password, database=database_name)
            cursor = conn.cursor()

            # Create table
            column_definitions = ', '.join([f'`{col}` TEXT' for col in df.columns])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions})")

            # Insert data
            placeholders = ', '.join(['%s'] * len(df.columns))
            insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({placeholders})"
            for row in df.itertuples(index=False):
                cursor.execute(insert_query, row)
            conn.commit()
            conn.close()
            print(f"Data imported successfully into '{table_name}'.")
            return True
        except Exception as e:
            print(f"Error importing data to MySQL: {e}")
            return False

    @staticmethod
    def import_to_mongodb(connection_string: str, database_name: str, input_file: str, collection_name: str, file_type: str = 'csv') -> bool:
        """
        Import CSV or JSON file to MongoDB.
        """
        try:
            client = MongoClient(connection_string)
            db = client[database_name]
            collection = db[collection_name]

            # Drop existing collection
            collection.drop()

            if file_type.lower() == 'csv':
                df = pd.read_csv(input_file)
                records = json.loads(df.to_json(orient='records'))
            else:  # JSON
                with open(input_file) as f:
                    records = json.load(f)

            collection.insert_many(records)
            print(f"Data imported successfully into MongoDB collection '{collection_name}'.")
            return True
        except Exception as e:
            print(f"Error importing data to MongoDB: {e}")
            return False


def validate_file(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Validate and analyze input file.
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        return {}

    try:
        if file_type.lower() == 'csv':
            df = pd.read_csv(file_path)
            return {
                'columns': list(df.columns),
                'row_count': len(df),
                'column_count': len(df.columns)
            }
        else:  # JSON
            with open(file_path) as f:
                data = json.load(f)
                return {
                    'record_count': len(data),
                    'keys': list(data[0].keys()) if data else []
                }
    except Exception as e:
        print(f"Error validating file: {e}")
        return {}


def setup_database():
    """
    Main database setup function.
    """
    print("\n=== Enhanced Database Setup Utility ===")

    while True:
        print("\nOptions:")
        print("1. Setup MySQL Database")
        print("2. Setup MongoDB Database")
        print("3. Validate Data File")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ")

        if choice == "1":
            print("\n--- MySQL Database Setup ---")
            host = input("Enter MySQL host (default: localhost): ") or "localhost"
            user = input("Enter MySQL user (default: root): ") or "root"
            password = input("Enter MySQL password: ")
            database_name = input("Enter new database name: ")
            file_path = input("Enter path to CSV file: ")
            table_name = input("Enter table name for the data: ")

            if validate_file(file_path, 'csv'):
                if DatabaseImporter.create_mysql_database(host, user, password, database_name):
                    DatabaseImporter.import_csv_to_mysql(host, user, password, database_name, file_path, table_name)

        elif choice == "2":
            print("\n--- MongoDB Database Setup ---")
            connection_string = input("Enter MongoDB connection string: ")
            database_name = input("Enter database name: ")
            file_type = input("Enter file type (csv/json): ").lower()
            file_path = input("Enter path to file: ")
            collection_name = input("Enter collection name for the data: ")

            if validate_file(file_path, file_type):
                DatabaseImporter.import_to_mongodb(connection_string, database_name, file_path, collection_name, file_type)

        elif choice == "3":
            file_path = input("Enter path to data file: ")
            file_type = input("Enter file type (csv/json): ").lower()
            validate_file(file_path, file_type)

        elif choice == "4":
            print("\nExiting database setup utility...")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    setup_database()
