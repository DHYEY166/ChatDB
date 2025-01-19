import mysql.connector
from pymongo import MongoClient
from typing import List, Dict, Optional, Union
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import json
import re


class ChatDB:
    def __init__(self):
        self.sql_db = None
        self.sql_cursor = None
        self.nosql_client = None
        self.nosql_db = None
        self.current_db = None
        self.current_db_type = None
        self.query_history = []
        self.last_error = None

    # Connect to SQL Database
    def connect_sql(self, connection_string: str) -> bool:
        try:
            import database_setup  # Ensure database_setup.py is in the same directory
            self.sql_db = database_setup.connect_to_sql(connection_string)
            self.sql_cursor = self.sql_db.cursor(dictionary=True)
            self.current_db_type = "sql"
            self.current_db = connection_string.split("/")[-1]  # Extract DB name
            return True
        except Exception as e:
            self.last_error = str(e)
            print(f"Error connecting to SQL database: {e}")
            return False

    # Connect to NoSQL Database
    def connect_nosql(self, connection_string: str, database_name: str) -> bool:
        try:
            self.nosql_client = MongoClient(connection_string)
            self.nosql_db = self.nosql_client[database_name]
            self.current_db_type = "nosql"
            self.current_db = database_name
            return True
        except Exception as e:
            self.last_error = str(e)
            print(f"Error connecting to NoSQL database: {e}")
            return False

    # List tables/collections
    def get_tables(self) -> List[str]:
        try:
            if self.current_db_type == "sql":
                self.sql_cursor.execute("SHOW TABLES")
                return [table["Tables_in_" + self.current_db] for table in self.sql_cursor.fetchall()]
            elif self.current_db_type == "nosql":
                return self.nosql_db.list_collection_names()
            else:
                raise Exception("No database connection established.")
        except Exception as e:
            self.last_error = str(e)
            print(f"Error listing tables/collections: {e}")
            return []

    # View sample data
    def get_sample_data(self, table_name: str, limit: int = 10) -> Optional[List[Dict]]:
        try:
            if self.current_db_type == "sql":
                self.sql_cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                return self.sql_cursor.fetchall()
            elif self.current_db_type == "nosql":
                return list(self.nosql_db[table_name].find().limit(limit))
            else:
                raise Exception("No database connection established.")
        except Exception as e:
            self.last_error = str(e)
            print(f"Error fetching sample data: {e}")
            return None

    # Execute a natural language query
    def process_natural_language_query(self, table_name: str, nl_query: str) -> Optional[List[Dict]]:
        try:
            if self.current_db_type == "sql":
                # Basic example for processing natural language query
                if "count" in nl_query.lower():
                    query = f"SELECT COUNT(*) as count FROM {table_name}"
                elif "last 30 days" in nl_query.lower():
                    query = f"SELECT * FROM {table_name} WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
                else:
                    query = f"SELECT * FROM {table_name}"

                self.sql_cursor.execute(query)
                return self.sql_cursor.fetchall()
            elif self.current_db_type == "nosql":
                # Example for natural language processing with MongoDB
                if "count" in nl_query.lower():
                    return [{"count": self.nosql_db[table_name].count_documents({})}]
                elif "last 30 days" in nl_query.lower():
                    return list(self.nosql_db[table_name].find({"date": {"$gte": datetime.now()}}))
                else:
                    return list(self.nosql_db[table_name].find().limit(10))
            else:
                raise Exception("No database connection established.")
        except Exception as e:
            self.last_error = str(e)
            print(f"Error processing natural language query: {e}")
            return None

    # Execute a custom query
    def execute_query(self, table_name: str, query: str) -> Optional[List[Dict]]:
        try:
            if self.current_db_type == "sql":
                self.sql_cursor.execute(query)
                return self.sql_cursor.fetchall()
            elif self.current_db_type == "nosql":
                return list(eval(query))
            else:
                raise Exception("No database connection established.")
        except Exception as e:
            self.last_error = str(e)
            print(f"Error executing custom query: {e}")
            return None

    # Visualize data
    def visualize_data(self, data: List[Dict], chart_type: str = 'bar', x_column: str = None, y_column: str = None):
        try:
            if not data:
                print("No data to visualize.")
                return

            df = pd.DataFrame(data)

            if not x_column:
                x_column = df.columns[0]
            if not y_column:
                y_column = df.columns[1]

            plt.figure(figsize=(10, 6))

            if chart_type == 'bar':
                df.plot.bar(x=x_column, y=y_column)
            elif chart_type == 'line':
                df.plot.line(x=x_column, y=y_column)
            elif chart_type == 'pie':
                df.set_index(x_column)[y_column].plot.pie(autopct='%1.1f%%')
            elif chart_type == 'scatter':
                df.plot.scatter(x=x_column, y=y_column)
            else:
                print(f"Unsupported chart type: {chart_type}")
                return

            plt.title(f"{chart_type.capitalize()} Chart")
            plt.xlabel(x_column)
            plt.ylabel(y_column)
            plt.show()
        except Exception as e:
            self.last_error = str(e)
            print(f"Error visualizing data: {e}")

    # Generate query suggestions
    def suggest_queries(self, table_name: str) -> List[str]:
        return [
            f"SELECT * FROM {table_name} LIMIT 10",
            f"SELECT COUNT(*) FROM {table_name}",
            f"SELECT * FROM {table_name} WHERE column_name = 'value'",
            f"SELECT column_name, COUNT(*) FROM {table_name} GROUP BY column_name",
        ]

    # Generate a database report
    def generate_report(self) -> Dict[str, Union[str, List[str], int]]:
        return {
            "database_type": self.current_db_type,
            "database_name": self.current_db,
            "tables": self.get_tables(),
            "queries_executed": len(self.query_history),
            "last_error": self.last_error
        }


if __name__ == "__main__":
    chatdb = ChatDB()
    print("ChatDB initialized. Use this class in your application.")
