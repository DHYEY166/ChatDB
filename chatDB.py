import mysql.connector
from pymongo import MongoClient
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import matplotlib.pyplot as plt
from tabulate import tabulate
import pandas as pd
from datetime import datetime, timedelta
import json
import numpy as np
from typing import Optional, List, Dict, Any, Union

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

class ChatDB:
    def __init__(self):
        self.sql_db = None
        self.sql_cursor = None
        self.nosql_client = None
        self.nosql_db = None
        self.current_db = None
        self.current_db_type = None
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.query_history = []
        self.last_error = None

    def connect_sql(self, host: str, user: str, password: str, database: str) -> bool:
        """Connect to MySQL database"""
        try:
            self.sql_db = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.sql_cursor = self.sql_db.cursor(dictionary=True)
            self.current_db = database
            self.current_db_type = "sql"
            return True
        except mysql.connector.Error as err:
            self.last_error = str(err)
            print(f"Error connecting to MySQL Database: {err}")
            return False

    def connect_nosql(self, connection_string: str, database: str) -> bool:
        """Connect to MongoDB database"""
        try:
            self.nosql_client = MongoClient(connection_string)
            self.nosql_db = self.nosql_client[database]
            self.current_db = database
            self.current_db_type = "nosql"
            return True
        except Exception as e:
            self.last_error = str(e)
            print(f"Error connecting to MongoDB: {e}")
            return False

    def get_tables(self) -> List[str]:
        """Get list of tables/collections in the current database"""
        if self.current_db_type == "sql":
            self.sql_cursor.execute("SHOW TABLES")
            tables = self.sql_cursor.fetchall()
            column_name = f'Tables_in_{self.current_db}'
            return [table[column_name] for table in tables]
        elif self.current_db_type == "nosql":
            return self.nosql_db.list_collection_names()
        return []

    def get_schema(self, table_name: str) -> Optional[Dict[str, str]]:
        """Get schema for a specific table/collection"""
        if self.current_db_type == "sql":
            try:
                self.sql_cursor.execute(f"DESCRIBE {table_name}")
                return {row['Field']: row['Type'] for row in self.sql_cursor.fetchall()}
            except mysql.connector.Error as err:
                self.last_error = str(err)
                print(f"Error getting schema: {err}")
                return None
        elif self.current_db_type == "nosql":
            try:
                sample = self.nosql_db[table_name].find_one()
                if sample:
                    return {k: type(v).__name__ for k, v in sample.items()}
            except Exception as e:
                self.last_error = str(e)
                print(f"Error getting schema: {e}")
                return None
        return None

    def get_sample_data(self, table_name: str, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Get sample data from table/collection"""
        if self.current_db_type == "sql":
            try:
                self.sql_cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                return self.sql_cursor.fetchall()
            except mysql.connector.Error as err:
                self.last_error = str(err)
                print(f"Error fetching sample data: {err}")
                return None
        elif self.current_db_type == "nosql":
            try:
                return list(self.nosql_db[table_name].find().limit(limit))
            except Exception as e:
                self.last_error = str(e)
                print(f"Error fetching sample data: {e}")
                return None
        return None
        
    def process_natural_language_query(self, table_name: str, nl_query: str) -> Optional[List[Dict[str, Any]]]:
        """Process natural language queries and convert them to database operations"""
        try:
            nl_query = nl_query.lower().strip()
            
            def extract_window_params(query_text: str) -> tuple:
                """Extract window function parameters"""
                partition_field = None
                order_field = None
                if 'partition by' in query_text:
                    words = query_text.split()
                    partition_field = words[words.index('by') + 1]
                if 'order by' in query_text:
                    words = query_text.split()
                    order_field = words[words.index('order') + 2]
                return partition_field, order_field

            def extract_date_range(query_text: str) -> Optional[str]:
                """Extract date range parameters"""
                date_patterns = {
                    'last (\d+) days': lambda x: f"DATE_SUB(CURDATE(), INTERVAL {x} DAY)",
                    'last (\d+) months': lambda x: f"DATE_SUB(CURDATE(), INTERVAL {x} MONTH)",
                    'last (\d+) years': lambda x: f"DATE_SUB(CURDATE(), INTERVAL {x} YEAR)"
                }
                for pattern, func in date_patterns.items():
                    match = re.search(pattern, query_text)
                    if match:
                        return func(match.group(1))
                return None

            def extract_aggregation_params(query_text: str) -> tuple:
                """Extract aggregation parameters"""
                agg_functions = ['sum', 'avg', 'min', 'max', 'count']
                field = None
                func = next((f for f in agg_functions if f in query_text), 'count')
                
                if func != 'count':
                    words = query_text.split()
                    try:
                        field = words[words.index(func) + 1]
                    except:
                        field = '*'
                return func, field

            if self.current_db_type == "nosql":
                # MongoDB query processing
                if 'join' in nl_query:
                    words = nl_query.split()
                    collection2 = words[words.index('join') + 1]
                    on_field = words[words.index('on') + 1]
                    
                    pipeline = [
                        {
                            '$lookup': {
                                'from': collection2,
                                'localField': on_field,
                                'foreignField': on_field,
                                'as': 'joined_data'
                            }
                        },
                        {'$unwind': '$joined_data'}
                    ]
                    return list(self.nosql_db[table_name].aggregate(pipeline))

                elif 'group by' in nl_query:
                    words = nl_query.split()
                    group_field = words[words.index('by') + 1]
                    agg_func, agg_field = extract_aggregation_params(nl_query)
                    
                    pipeline = [
                        {'$group': {
                            '_id': f'${group_field}',
                            'result': {
                                f'${agg_func}': f'${agg_field}' if agg_field else 1
                            }
                        }}
                    ]
                    return list(self.nosql_db[table_name].aggregate(pipeline))

                elif 'rank' in nl_query or 'dense rank' in nl_query:
                    words = nl_query.split()
                    sort_field = words[words.index('by') + 1] if 'by' in words else '_id'
                    partition_field = words[words.index('partition') + 2] if 'partition' in words else None
                    
                    pipeline = [
                        {'$setWindowFields': {
                            'partitionBy': f'${partition_field}' if partition_field else None,
                            'sortBy': {sort_field: 1},
                            'output': {
                                'rank': {
                                    '$rank': {}
                                }
                            }
                        }}
                    ]
                    return list(self.nosql_db[table_name].aggregate(pipeline))

                elif 'moving average' in nl_query:
                    words = nl_query.split()
                    field = words[words.index('average') + 1]
                    window_size = int(words[words.index('window') + 1]) if 'window' in words else 3
                    
                    pipeline = [
                        {'$setWindowFields': {
                            'sortBy': {'_id': 1},
                            'output': {
                                'movingAvg': {
                                    '$avg': f'${field}',
                                    'window': {'documents': [-window_size, 0]}
                                }
                            }
                        }}
                    ]
                    return list(self.nosql_db[table_name].aggregate(pipeline))

            else:
                # SQL query processing
                if 'join' in nl_query:
                    join_type = 'INNER JOIN'
                    if 'left join' in nl_query:
                        join_type = 'LEFT JOIN'
                    elif 'right join' in nl_query:
                        join_type = 'RIGHT JOIN'
                    elif 'outer join' in nl_query:
                        join_type = 'FULL OUTER JOIN'
                        
                    words = nl_query.split()
                    table2 = words[words.index('join') + 1]
                    join_field = words[words.index('on') + 1]
                    
                    query = f"""
                    SELECT *
                    FROM {table_name}
                    {join_type} {table2}
                    ON {table_name}.{join_field} = {table2}.{join_field}
                    """
                    return self.execute_query(table_name, query)

                elif 'group by' in nl_query:
                    words = nl_query.split()
                    group_field = words[words.index('by') + 1]
                    agg_func, agg_field = extract_aggregation_params(nl_query)
                    
                    query = f"""
                    SELECT {group_field},
                           {agg_func.upper()}({agg_field}) as result
                    FROM {table_name}
                    GROUP BY {group_field}
                    """
                    return self.execute_query(table_name, query)

                else:
                    query = f"SELECT * FROM {table_name}"
                    return self.execute_query(table_name, query)
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Error processing query: {e}")
            return None
            
    def execute_query(self, table_name: Optional[str], query: Union[str, List[Dict]]) -> Optional[List[Dict[str, Any]]]:
        """Execute raw query on the current database"""
        try:
            if self.current_db_type == "sql":
                self.sql_cursor.execute(query)
                result = self.sql_cursor.fetchall()
                self.query_history.append({"query": query, "timestamp": datetime.now()})
                return result
            elif self.current_db_type == "nosql":
                if isinstance(query, str):
                    if query == "show all data":
                        pipeline = []
                    else:
                        try:
                            pipeline = eval(query)
                        except:
                            pipeline = [{'$match': {}}]
                else:
                    pipeline = query
                result = list(self.nosql_db[table_name].aggregate(pipeline))
                self.query_history.append({
                    "pipeline": pipeline,
                    "timestamp": datetime.now()
                })
                return result
        except Exception as e:
            self.last_error = str(e)
            print(f"Error executing query: {e}")
            return None

    def visualize_data(self, data: List[Dict[str, Any]], chart_type: str = 'bar',
                      x_column: Optional[str] = None, y_column: Optional[str] = None) -> None:
        if not data:
            print("No data to visualize")
            return

        try:
            plt.close('all')
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            print("\nOriginal DataFrame:")
            print(df)
            
            # Set default columns for aggregation results
            if not x_column:
                x_column = 'store_location' if 'store_location' in df.columns else df.columns[0]
            if not y_column:
                y_column = 'result' if 'result' in df.columns else df.columns[1]
            
            print(f"\nUsing columns: x={x_column}, y={y_column}")
            
            # Ensure numeric conversion for y-axis
            try:
                df[y_column] = df[y_column].apply(lambda x: float(str(x).replace(',', '')))
            except Exception as e:
                print(f"Error converting to numeric: {e}")
                return
            
            plt.figure(figsize=(10, 6))
            
            if chart_type == 'bar':
                plt.bar(range(len(df)), df[y_column])
                plt.xticks(range(len(df)), df[x_column], rotation=45, ha='right')
            
            elif chart_type == 'pie':
                plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%')
            
            elif chart_type == 'line':
                plt.plot(range(len(df)), df[y_column], marker='o')
                plt.xticks(range(len(df)), df[x_column], rotation=45, ha='right')
            
            elif chart_type == 'scatter':
                plt.scatter(range(len(df)), df[y_column])
                plt.xticks(range(len(df)), df[x_column], rotation=45, ha='right')
            
            elif chart_type == 'histogram':
                plt.hist(df[y_column].values, bins=min(10, len(df[y_column].unique())))
            
            elif chart_type == 'box':
                plt.boxplot(df[y_column].values)
                plt.xticks([1], [y_column])
            
            plt.title(f"Store Locations and Quantities")
            
            if chart_type != 'pie':
                plt.xlabel("Store Location")
                plt.ylabel("Total Quantity")
                plt.grid(True, linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            plt.show()
            plt.close()

        except Exception as e:
            self.last_error = str(e)
            print(f"\nError visualizing data: {e}")
            print("\nData structure:")
            for row in data[:2]:
                print(row)
            plt.close('all')

    def suggest_queries(self, table_name: str) -> List[str]:
        """Generate query suggestions based on schema"""
        schema = self.get_schema(table_name)
        suggestions = []
        
        if self.current_db_type == "sql":
            suggestions.extend([
                f"Show me all data from {table_name}",
                f"Count total records in {table_name}",
                f"Join {table_name} with another_table on id",
                f"Group by category and show count",
                f"Calculate running total of amount",
                f"Show rank by value partition by category",
                f"Calculate moving average of price window 3",
                f"Show data from last 30 days",
                f"Show 95th percentile of value",
                f"Pivot data by category values amount"
            ])
        else:
            suggestions.extend([
                "show all data",
                "count all records",
                "join collection2 on _id",
                "group by category and count",
                "calculate running total of amount",
                "rank by value partition by category",
                "moving average of price window 3",
                "pivot by category values amount"
            ])
        
        return suggestions

    def generate_report(self) -> Dict[str, Any]:
        """Generate database usage report"""
        report = {
            "database_type": self.current_db_type,
            "database_name": self.current_db,
            "tables": self.get_tables(),
            "queries_executed": len(self.query_history),
            "last_query_time": self.query_history[-1]["timestamp"] if self.query_history else None,
            "last_error": self.last_error
        }
        return report

def print_table(data: List[Dict[str, Any]]) -> None:
    """Print data in tabulated format"""
    if not data:
        print("No data to display")
        return
    try:
        # Convert ObjectId to string for MongoDB results
        if isinstance(data, list) and len(data) > 0 and '_id' in data[0]:
            for item in data:
                item['_id'] = str(item['_id'])
        print(tabulate(data, headers="keys", tablefmt="grid"))
    except Exception as e:
        print(f"Error displaying table: {e}")

def main():
    chatdb = ChatDB()
    
    while True:
        print("\n=== ChatDB Menu ===")
        print("1. Connect to SQL Database")
        print("2. Connect to NoSQL Database")
        print("3. List tables/collections")
        print("4. View sample data")
        print("5. Execute natural language query")
        print("6. Execute custom query")
        print("7. Visualize data")
        print("8. Get query suggestions")
        print("9. Generate database report")
        print("10. Exit")
        
        choice = input("\nEnter your choice (1-10): ")
        
        if choice == "1":
            host = input("Enter MySQL host: ")
            user = input("Enter MySQL user: ")
            password = input("Enter MySQL password: ")
            database = input("Enter MySQL database name: ")
            if chatdb.connect_sql(host, user, password, database):
                print(f"Successfully connected to MySQL database: {database}")
            else:
                print("Failed to connect to MySQL database.")
        
        elif choice == "2":
            connection_string = input("Enter MongoDB connection string: ")
            database = input("Enter MongoDB database name: ")
            if chatdb.connect_nosql(connection_string, database):
                print(f"Successfully connected to MongoDB database: {database}")
            else:
                print("Failed to connect to MongoDB database.")
        
        elif choice == "3":
            if not chatdb.current_db:
                print("Please connect to a database first.")
                continue
            tables = chatdb.get_tables()
            print(f"\nAvailable tables in {chatdb.current_db}:")
            for table in tables:
                print(f"- {table}")
        
        elif choice == "4":
            if not chatdb.current_db:
                print("Please connect to a database first.")
                continue
            table_name = input("Enter table name: ")
            sample_data = chatdb.get_sample_data(table_name)
            if sample_data:
                print(f"\nSample data from {table_name}:")
                print_table(sample_data)
        
        elif choice == "5":
            if not chatdb.current_db:
                print("Please connect to a database first.")
                continue
            table_name = input("Enter table name: ")
            query = input("Enter your natural language query: ")
            result = chatdb.process_natural_language_query(table_name, query)
            if result:
                print("\nQuery result:")
                print_table(result)
        
        elif choice == "6":
            if not chatdb.current_db:
                print("Please connect to a database first.")
                continue
            table_name = input("Enter table name: ")
            print("\nEnter your custom query:")
            query = input()
            result = chatdb.execute_query(table_name, query)
            if result:
                print("\nQuery result:")
                print_table(result)
        
        elif choice == "7":
            if not chatdb.current_db:
                print("Please connect to a database first.")
                continue
            table_name = input("Enter table name: ")
            query = input("Enter your query: ")
            result = chatdb.process_natural_language_query(table_name, query)
            if result:
                print("\nQuery result:")
                print_table(result)
                chart_type = input("Enter chart type (bar/line/scatter/pie/histogram/box): ").lower()
                x_col = input("Enter x-axis column (or press Enter for default): ") or None
                y_col = input("Enter y-axis column (or press Enter for default): ") or None
                chatdb.visualize_data(result, chart_type, x_col, y_col)
        
        elif choice == "8":
            if not chatdb.current_db:
                print("Please connect to a database first.")
                continue
            table_name = input("Enter table name: ")
            suggestions = chatdb.suggest_queries(table_name)
            print("\nQuery Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"{i}. {suggestion}")
        
        elif choice == "9":
            if not chatdb.current_db:
                print("Please connect to a database first.")
                continue
            report = chatdb.generate_report()
            print("\nDatabase Report:")
            print(json.dumps(report, indent=2, default=str))
        
        elif choice == "10":
            if chatdb.sql_db:
                chatdb.sql_db.close()
            if chatdb.nosql_client:
                chatdb.nosql_client.close()
            print("\nThank you for using ChatDB. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
