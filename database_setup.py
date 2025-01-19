import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
from pymongo import MongoClient, ASCENDING, DESCENDING
import os
import numpy as np
import json
from datetime import datetime
import warnings
from typing import Optional, List, Dict, Any, Union
import re
from pathlib import Path
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

class DatabaseImporter:
    @staticmethod
    
    def try_parse_date(value):    # Add the function here
        common_formats = [
            '%Y-%m-%d',           # 2023-12-28
            '%d/%m/%Y',           # 28/12/2023
            '%m/%d/%Y',           # 12/28/2023
            '%Y/%m/%d',           # 2023/12/28
            '%d-%m-%Y',           # 28-12-2023
            '%Y-%m-%d %H:%M:%S',  # 2023-12-28 14:30:00
            '%m/%d/%Y %H:%M'      # 12/28/2023 14:30
        ]
        
        for fmt in common_formats:
            try:
                return pd.to_datetime(value, format=fmt)
            except:
                continue
        
        try:
            return pd.to_datetime(value)
        except:
            return None
    
    def get_mysql_type(dtype) -> str:
        """Enhanced data type conversion for MySQL"""
        if pd.api.types.is_integer_dtype(dtype):
            return "INT"
        elif pd.api.types.is_float_dtype(dtype):
            return "DECIMAL(20,6)"  # Increased precision for analytics
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return "DATETIME(6)"    # Added microsecond precision
        elif pd.api.types.is_bool_dtype(dtype):
            return "BOOLEAN"
        elif pd.api.types.is_string_dtype(dtype):
            return "VARCHAR(1000)"  # Increased length for text
        else:
            return "JSON"          # Added JSON type support

    @staticmethod
    def create_mysql_database(host: str, user: str, password: str, database_name: str) -> bool:
        """Create MySQL database with optimized settings"""
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password
            )
            cursor = conn.cursor()

            # Create database with proper character set and collation
            cursor.execute(f"DROP DATABASE IF EXISTS {database_name}")
            cursor.execute(f"""
                CREATE DATABASE {database_name}
                CHARACTER SET utf8mb4
                COLLATE utf8mb4_unicode_ci
            """)
            print(f"Database '{database_name}' created successfully")

            # Create user with enhanced privileges for analytics
            cursor.execute(f"""
                CREATE USER IF NOT EXISTS 'chatdb_user'@'localhost'
                IDENTIFIED BY 'your_password'
            """)
            cursor.execute(f"GRANT ALL PRIVILEGES ON {database_name}.* TO 'chatdb_user'@'localhost'")
            cursor.execute("GRANT PROCESS ON *.* TO 'chatdb_user'@'localhost'")  # For monitoring
            cursor.execute("FLUSH PRIVILEGES")
            print("User 'chatdb_user' created with enhanced privileges")

            # Set optimal database configuration for analytics
            cursor.execute(f"USE {database_name}")
            optimizations = [
                "SET GLOBAL innodb_buffer_pool_size = 1073741824",  # 1GB buffer pool
                "SET GLOBAL innodb_file_per_table = 1",
                "SET GLOBAL innodb_stats_on_metadata = 0",
                "SET GLOBAL innodb_buffer_pool_instances = 8",
                "SET GLOBAL innodb_read_io_threads = 8",
                "SET GLOBAL innodb_write_io_threads = 8",
                "SET GLOBAL innodb_io_capacity = 2000",
                "SET GLOBAL innodb_io_capacity_max = 4000"
            ]
            
            for opt in optimizations:
                try:
                    cursor.execute(opt)
                except mysql.connector.Error:
                    continue  # Skip if not enough privileges

            conn.close()
            return True
        except Exception as e:
            print(f"Error creating MySQL database: {e}")
            return False

    @staticmethod
    def analyze_csv_file(file_path: str) -> Dict[str, Any]:
        """Analyze CSV file structure and content"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            df = pd.read_csv(file_path)
            
            analysis = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": {},
                "sample_rows": df.head(3).to_dict('records'),
                "missing_values": df.isnull().sum().to_dict(),
                "unique_values": {col: df[col].nunique() for col in df.columns},
                "memory_usage": df.memory_usage(deep=True).sum() / 1024**2  # MB
            }

            for column in df.columns:
                col_info = {
                    "dtype": str(df[column].dtype),
                    "unique_count": df[column].nunique(),
                    "missing_count": df[column].isnull().sum(),
                    "sample_values": df[column].dropna().head(3).tolist()
                }
                
                # Additional numeric column statistics
                if pd.api.types.is_numeric_dtype(df[column]):
                    col_info.update({
                        "min": float(df[column].min()),
                        "max": float(df[column].max()),
                        "mean": float(df[column].mean()),
                        "median": float(df[column].median()),
                        "std": float(df[column].std())
                    })
                
                # String column statistics
                elif pd.api.types.is_string_dtype(df[column]):
                    non_null_values = df[column].dropna()
                    if len(non_null_values) > 0:
                        col_info.update({
                            "min_length": min(non_null_values.str.len()),
                            "max_length": max(non_null_values.str.len()),
                            "avg_length": np.mean(non_null_values.str.len())
                        })

                # Date detection
                if pd.api.types.is_string_dtype(df[column]):
                    sample_values = df[column].dropna().head()
                    if all(DatabaseImporter.try_parse_date(val) is not None for val in sample_values):
                        col_info["potential_date"] = True
                    else:
                        col_info["potential_date"] = False

                analysis["columns"][column] = col_info

            # Additional dataset-level analysis
            analysis["correlation_matrix"] = None
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                analysis["correlation_matrix"] = df[numeric_cols].corr().to_dict()

            return analysis
        except Exception as e:
            print(f"Error analyzing CSV file: {e}")
            return {}

    @staticmethod
    def analyze_json_file(file_path: str) -> Dict[str, Any]:
        """Analyze JSON file structure and content"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(file_path, 'r') as f:
                content = f.read()

            # Try different JSON formats
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Try as JSON Lines
                data = [json.loads(line) for line in content.splitlines() if line.strip()]

            if not isinstance(data, list):
                data = [data]

            analysis = {
                "record_count": len(data),
                "structure": {},
                "sample_records": data[:3],
                "field_types": {},
                "nested_objects": [],
                "arrays": [],
                "memory_usage": len(content) / 1024**2  # MB
            }

            def analyze_field(field_data: Any, prefix: str = "") -> Dict[str, Any]:
                field_info = {
                    "type": type(field_data).__name__,
                    "sample_value": str(field_data)[:100]
                }

                if isinstance(field_data, (int, float)):
                    values = [rec.get(prefix) for rec in data if isinstance(rec.get(prefix), (int, float))]
                    if values:
                        field_info.update({
                            "min": min(values),
                            "max": max(values),
                            "mean": sum(values) / len(values)
                        })
                elif isinstance(field_data, str):
                    field_info["length"] = len(field_data)
                    # Try date parsing
                    try:
                        datetime.fromisoformat(field_data.replace('Z', '+00:00'))
                        field_info["potential_date"] = True
                    except:
                        field_info["potential_date"] = False

                return field_info

            # Analyze structure of first record to get field information
            def analyze_structure(obj: Any, prefix: str = "") -> None:
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        analysis["structure"][full_key] = analyze_field(value, full_key)
                        if isinstance(value, dict):
                            analysis["nested_objects"].append(full_key)
                            analyze_structure(value, full_key)
                        elif isinstance(value, list):
                            analysis["arrays"].append(full_key)
                            if value and isinstance(value[0], dict):
                                analyze_structure(value[0], f"{full_key}[]")

            if data:
                analyze_structure(data[0])

            return analysis
        except Exception as e:
            print(f"Error analyzing JSON file: {e}")
            return {}
            

    @staticmethod
    def import_csv_to_mysql(host: str, user: str, password: str, database_name: str,
                          csv_file: str, table_name: str) -> bool:
        """Import CSV file to MySQL with optimizations"""
        try:
            # Read CSV file with enhanced options
            df = pd.read_csv(csv_file,
                           parse_dates=True,
                           low_memory=False)
            
            # First identify date and numeric columns
            date_cols = []
            numeric_cols = []
            for column, dtype in df.dtypes.items():
                if pd.api.types.is_datetime64_dtype(dtype):
                    date_cols.append(column)
                elif pd.api.types.is_numeric_dtype(dtype):
                    numeric_cols.append(column)
                # Updated date detection code ↓
                elif pd.api.types.is_string_dtype(dtype):
                    try:
                        sample_dates = pd.to_datetime(df[column].dropna().head())
                        if (sample_dates != pd.Timestamp(0)).any():
                            date_cols.append(column)
                    except:
                        pass

            # Automatic date detection and conversion
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        pd.to_datetime(df[col].dropna().head())
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass

            # Create MySQL connection
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database_name
            )
            cursor = conn.cursor()

            # Create table with optimized schema
            columns = []
            indexes = []
            
            for column, dtype in df.dtypes.items():
                mysql_type = DatabaseImporter.get_mysql_type(dtype)
                col_name = re.sub(r'\W+', '_', column.lower())  # Sanitize column names
                
                # Modify VARCHAR length for indexed columns
                if mysql_type.startswith('VARCHAR'):
                    if any(keyword in col_name.lower() for keyword in
                          ['id', 'key', 'code', 'date', 'category', 'type', 'status']):
                        mysql_type = 'VARCHAR(255)'  # Shorter length for indexed columns
                
                columns.append(f"`{col_name}` {mysql_type}")
                
                # Create indexes with length limits for string columns
                if any(keyword in col_name.lower() for keyword in
                      ['id', 'key', 'code', 'date', 'category', 'type', 'status']):
                    if mysql_type.startswith('VARCHAR'):
                        indexes.append(f"INDEX idx_{col_name} (`{col_name}`(191))")
                    else:
                        indexes.append(f"INDEX idx_{col_name} (`{col_name}`)")
                
                # Create indexes for columns with high selectivity
                unique_ratio = df[column].nunique() / len(df)
                if 0.01 <= unique_ratio <= 0.5:
                    if mysql_type.startswith('VARCHAR'):
                        indexes.append(f"INDEX idx_sel_{col_name} (`{col_name}`(191))")
                    else:
                        indexes.append(f"INDEX idx_sel_{col_name} (`{col_name}`)")

            # Add composite indexes for analytics
            if date_cols and numeric_cols:
                for date_col in date_cols[:2]:
                    for num_col in numeric_cols[:3]:
                        date_col_name = re.sub(r'\W+', '_', date_col.lower())
                        num_col_name = re.sub(r'\W+', '_', num_col.lower())
                        date_type = df[date_col].dtype
                        num_type = df[num_col].dtype
                        
                        index_cols = []
                        if pd.api.types.is_string_dtype(date_type):
                            index_cols.append(f"`{date_col_name}`(191)")
                        else:
                            index_cols.append(f"`{date_col_name}`")
                            
                        if pd.api.types.is_string_dtype(num_type):
                            index_cols.append(f"`{num_col_name}`(191)")
                        else:
                            index_cols.append(f"`{num_col_name}`")
                            
                        indexes.append(
                            f"INDEX idx_analytics_{date_col_name}_{num_col_name} "
                            f"({', '.join(index_cols)})"
                        )

            # Create table with all optimizations
            create_table_query = f"""
            CREATE TABLE {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                {', '.join(columns)},
                {', '.join(indexes)}
            ) ENGINE=InnoDB
            """
            cursor.execute(create_table_query)
            cursor.fetchall()  # Consume the result
            print(f"Created table with optimized schema and indexes:\n{create_table_query}")
            
            # Prepare column names for insert
            column_names = [re.sub(r'\W+', '_', col.lower()) for col in df.columns]
            
            # Insert data in optimized batches
            batch_size = 5000
            total_batches = len(df) // batch_size + 1
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                placeholders = ', '.join(['%s'] * len(df.columns))
                insert_query = f"""
                    INSERT INTO {table_name} 
                    ({', '.join([f'`{col}`' for col in column_names])})
                    VALUES ({placeholders})
                """
                values = [tuple(x) for x in batch.replace({np.nan: None}).values]
                
                cursor.executemany(insert_query, values)
                conn.commit()
                print(f"Inserted batch {i//batch_size + 1}/{total_batches}")

            # Create additional statistics
            print("\nGathering table statistics...")
            try:
                # Consume any pending results
                while cursor.nextset():
                    pass
                
                cursor.execute(f"ANALYZE TABLE {table_name}")
                cursor.fetchall()  # Consume the result
                
                cursor.execute(f"OPTIMIZE TABLE {table_name}")
                cursor.fetchall()  # Consume the result

                # Create views for common analytics queries
                print("\nCreating analytics views...")
                if date_cols:
                    main_date_col = date_cols[0]
                    main_date_col_name = re.sub(r'\W+', '_', main_date_col.lower())
                    
                    # Daily aggregation view
                    agg_columns = []
                    for col in numeric_cols[:5]:
                        safe_col = re.sub(r'\W+', '_', col.lower())
                        agg_columns.append(f", SUM(`{safe_col}`) as sum_{safe_col}")

                    cursor.execute(f"""
                        CREATE OR REPLACE VIEW v_{table_name}_daily AS
                        SELECT 
                            DATE({main_date_col_name}) as date,
                            COUNT(*) as record_count
                            {' '.join(agg_columns)}
                        FROM {table_name}
                        GROUP BY DATE({main_date_col_name})
                    """)
                    cursor.fetchall()  # Consume the result
                    
                    # Monthly aggregation view
                    cursor.execute(f"""
                        CREATE OR REPLACE VIEW v_{table_name}_monthly AS
                        SELECT 
                            DATE_FORMAT({main_date_col_name}, '%Y-%m-01') as month,
                            COUNT(*) as record_count
                            {' '.join(agg_columns)}
                        FROM {table_name}
                        GROUP BY DATE_FORMAT({main_date_col_name}, '%Y-%m-01')
                    """)
                    cursor.fetchall()  # Consume the result

            except mysql.connector.Error as err:
                print(f"Warning: Error during statistics gathering: {err}")
                # Continue execution even if statistics gathering fails
                pass

            conn.close()
            print(f"\nData imported successfully to MySQL table '{table_name}'")
            return True

        except Exception as e:
            print(f"Error importing data to MySQL: {e}")
            if 'conn' in locals() and conn.is_connected():
                conn.close()
            return False

    @staticmethod
    def import_to_mongodb(connection_string: str, database_name: str,
                         input_file: str, collection_name: str, file_type: str = 'csv') -> bool:
        """Import CSV or JSON file to MongoDB with optimizations"""
        try:
            # Connect to MongoDB
            client = MongoClient(connection_string)
            db = client[database_name]
            collection = db[collection_name]

            # Drop existing collection
            collection.drop()

            # Process input file based on type
            if file_type.lower() == 'csv':
                df = pd.read_csv(input_file, parse_dates=True, infer_datetime_format=True)
                
                # Convert DataFrame to records
                records = json.loads(
                    df.to_json(orient='records', date_format='iso', default_handler=str)
                )
            else:  # JSON
                with open(input_file) as f:
                    content = f.read()
                    try:
                        # Try as regular JSON
                        data = json.loads(content)
                        records = data if isinstance(data, list) else [data]
                    except json.JSONDecodeError:
                        # Try as JSON Lines
                        records = [json.loads(line) for line in content.splitlines() if line.strip()]

            # Create indexes for optimization
            print("\nAnalyzing data for index creation...")
            if records:
                sample_doc = records[0]
                
                def create_indexes_recursive(doc: Dict, prefix: str = ""):
                    for key, value in doc.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        
                        # Create single-field indexes
                        if any(keyword in key.lower() for keyword in
                              ['id', 'key', 'code', 'date', 'category', 'type', 'status']):
                            collection.create_index([(full_key, ASCENDING)], background=True)
                            print(f"Created index for {full_key}")
                        
                        # Create text indexes for string fields
                        if isinstance(value, str) and len(value.split()) > 1:
                            try:
                                collection.create_index([(full_key, "text")], background=True)
                                print(f"Created text index for {full_key}")
                            except:
                                pass

                        # Recursively process nested documents
                        if isinstance(value, dict):
                            create_indexes_recursive(value, full_key)
                        elif isinstance(value, list) and value and isinstance(value[0], dict):
                            create_indexes_recursive(value[0], f"{full_key}")

                create_indexes_recursive(sample_doc)

                # Create compound indexes for common queries
                date_fields = []
                numeric_fields = []
                
                def identify_field_types(doc: Dict, prefix: str = ""):
                    for key, value in doc.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, str):
                            try:
                                datetime.fromisoformat(value.replace('Z', '+00:00'))
                                date_fields.append(full_key)
                            except:
                                pass
                        elif isinstance(value, (int, float)):
                            numeric_fields.append(full_key)
                        elif isinstance(value, dict):
                            identify_field_types(value, full_key)

                identify_field_types(sample_doc)

                # Create compound indexes for date-numeric combinations
                for date_field in date_fields[:2]:  # Limit to 2 date fields
                    for numeric_field in numeric_fields[:3]:  # Limit to 3 numeric fields
                        collection.create_index([
                            (date_field, ASCENDING),
                            (numeric_field, ASCENDING)
                        ], background=True)
                        print(f"Created compound index for {date_field} and {numeric_field}")

            # Insert documents in optimized batches
            batch_size = 5000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                collection.insert_many(batch)
                print(f"Inserted records {i} to {min(i + batch_size, len(records))}")

            print(f"\nData imported successfully to MongoDB collection '{collection_name}'")
            
            # Create example queries documentation
            print("\nExample queries you can now run:")
            print("1. Basic queries:")
            print(f"   - db.{collection_name}.find({{}})")
            if date_fields:
                print(f"   - db.{collection_name}.find({{ {date_fields[0]}: {{ $gte: ISODate('2023-01-01') }} }})")
            if numeric_fields:
                print(f"   - db.{collection_name}.find({{ {numeric_fields[0]}: {{ $gt: 100 }} }})")
            
            print("\n2. Aggregation queries:")
            if date_fields and numeric_fields:
                print(f"""   - db.{collection_name}.aggregate([
                    {{ $group: {{
                        _id: {{ $dateToString: {{ format: "%Y-%m", date: "${date_fields[0]}" }} }},
                        total: {{ $sum: "${numeric_fields[0]}" }}
                    }} }}
                ])""")
            
            return True

        except Exception as e:
            print(f"Error importing data to MongoDB: {e}")
            return False
    
    
def validate_file(file_path: str, file_type: str) -> Dict[str, Any]:
    """Validate and analyze input file"""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        return {}

    try:
        if file_type.lower() == 'csv':
            analysis = DatabaseImporter.analyze_csv_file(file_path)
            
            print("\nCSV File Analysis:")
            print(f"Total rows: {analysis['row_count']}")
            print(f"Total columns: {analysis['column_count']}")
            print(f"Memory usage: {analysis['memory_usage']:.2f} MB")
            
            print("\nColumn Details:")
            for col, info in analysis['columns'].items():
                print(f"\n{col}:")
                print(f"  Type: {info['dtype']}")
                print(f"  Unique values: {info['unique_count']}")
                print(f"  Missing values: {info['missing_count']}")
                if 'min' in info:
                    print(f"  Range: {info['min']} to {info['max']}")
                if 'potential_date' in info:
                    print(f"  Potential date field: {info['potential_date']}")
                
            return analysis

        else:  # JSON
            analysis = DatabaseImporter.analyze_json_file(file_path)
            
            print("\nJSON File Analysis:")
            print(f"Total records: {analysis['record_count']}")
            print(f"Memory usage: {analysis['memory_usage']:.2f} MB")
            
            if analysis['nested_objects']:
                print("\nNested objects found in:")
                for obj in analysis['nested_objects']:
                    print(f"  - {obj}")
            
            if analysis['arrays']:
                print("\nArray fields found in:")
                for arr in analysis['arrays']:
                    print(f"  - {arr}")
            
            print("\nField Details:")
            for field, info in analysis['structure'].items():
                print(f"\n{field}:")
                print(f"  Type: {info['type']}")
                if 'min' in info:
                    print(f"  Range: {info['min']} to {info['max']}")
                if 'potential_date' in info:
                    print(f"  Potential date field: {info['potential_date']}")
            
            return analysis

    except Exception as e:
        print(f"Error validating file: {e}")
        return {}

def generate_query_examples(file_analysis: Dict[str, Any], db_type: str, table_name: str) -> List[str]:
    """Generate example queries based on file analysis"""
    queries = []
    
    if db_type.lower() == 'mysql':
        # Basic queries
        queries.append(f"SELECT * FROM {table_name} LIMIT 10;")
        queries.append(f"SELECT COUNT(*) FROM {table_name};")
        
        if file_analysis.get('columns'):
            # Find date columns
            date_cols = [col for col, info in file_analysis['columns'].items()
                        if info.get('potential_date')]
            
            # Find numeric columns
            numeric_cols = [col for col, info in file_analysis['columns'].items()
                          if 'mean' in info]
            
            # Generate date-based queries
            if date_cols:
                date_col = date_cols[0]
                queries.extend([
                    f"SELECT DATE({date_col}), COUNT(*) FROM {table_name} GROUP BY DATE({date_col});",
                    f"SELECT * FROM {table_name} WHERE {date_col} >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);"
                ])
            
            # Generate aggregation queries
            if numeric_cols:
                num_col = numeric_cols[0]
                queries.extend([
                    f"SELECT AVG({num_col}), MAX({num_col}), MIN({num_col}) FROM {table_name};",
                    f"SELECT {num_col}, COUNT(*) FROM {table_name} GROUP BY {num_col} ORDER BY COUNT(*) DESC LIMIT 5;"
                ])
            
            # Generate window function queries
            if numeric_cols and len(numeric_cols) >= 2:
                queries.append(f"""
                    SELECT *, 
                           RANK() OVER (ORDER BY {numeric_cols[0]} DESC) as rank,
                           AVG({numeric_cols[1]}) OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as moving_avg
                    FROM {table_name};
                """)
    
    else:  # MongoDB
        # Basic queries
        queries.append(f"db.{table_name}.find({{}})")
        queries.append(f"db.{table_name}.countDocuments({{}})")
        
        if file_analysis.get('structure'):
            # Find date fields
            date_fields = [field for field, info in file_analysis['structure'].items()
                          if info.get('potential_date')]
            
            # Find numeric fields
            numeric_fields = [field for field, info in file_analysis['structure'].items()
                            if info['type'] in ('int', 'float')]
            
            # Generate date-based queries
            if date_fields:
                date_field = date_fields[0]
                queries.extend([
                    f"""db.{table_name}.aggregate([
                        {{ $group: {{
                            _id: {{ $dateToString: {{ format: "%Y-%m-%d", date: "${date_field}" }} }},
                            count: {{ $sum: 1 }}
                        }} }}
                    ])""",
                    f"""db.{table_name}.find({{
                        {date_field}: {{ 
                            $gte: new Date(new Date().setDate(new Date().getDate() - 30))
                        }}
                    }})"""
                ])
            
            # Generate aggregation queries
            if numeric_fields:
                num_field = numeric_fields[0]
                queries.extend([
                    f"""db.{table_name}.aggregate([
                        {{ $group: {{
                            _id: null,
                            avg: {{ $avg: "${num_field}" }},
                            max: {{ $max: "${num_field}" }},
                            min: {{ $min: "${num_field}" }}
                        }} }}
                    ])""",
                    f"""db.{table_name}.aggregate([
                        {{ $sort: {{ {num_field}: -1 }} }},
                        {{ $limit: 5 }}
                    ])"""
                ])
    
    return queries

def setup_database():
    """Main database setup function"""
    print("\n=== Enhanced Database Setup Utility ===")
    
    while True:
        print("\nOptions:")
        print("1. Setup MySQL Database")
        print("2. Setup MongoDB Database")
        print("3. Validate Data File")
        print("4. Generate Query Examples")
        print("5. Exit")

        choice = input("\nEnter your choice (1-5): ")

        if choice == "1":
            print("\n--- MySQL Database Setup ---")
            host = input("Enter MySQL host (default: localhost): ") or "localhost"
            user = input("Enter MySQL root user (default: root): ") or "root"
            password = input("Enter MySQL root password: ")
            database_name = input("Enter new database name: ")
            file_path = input("Enter path to CSV file: ")
            table_name = input("Enter table name for the data: ")

            # Validate file first
            analysis = validate_file(file_path, 'csv')
            if analysis:
                if input("\nProceed with database creation? (y/n): ").lower() == 'y':
                    if DatabaseImporter.create_mysql_database(host, user, password, database_name):
                        if DatabaseImporter.import_csv_to_mysql(host, user, password, database_name, file_path, table_name):
                            print("\nGenerated query examples:")
                            for query in generate_query_examples(analysis, 'mysql', table_name):
                                print(f"\n{query}")

        elif choice == "2":
            print("\n--- MongoDB Database Setup ---")
            connection_string = input("Enter MongoDB connection string (default: mongodb://localhost:27017/): ") or "mongodb://localhost:27017/"
            database_name = input("Enter database name: ")
            file_type = input("Enter file type (csv/json): ").lower()
            file_path = input("Enter path to file: ")
            collection_name = input("Enter collection name for the data: ")

            # Validate file first
            analysis = validate_file(file_path, file_type)
            if analysis:
                if input("\nProceed with database creation? (y/n): ").lower() == 'y':
                    if DatabaseImporter.import_to_mongodb(connection_string, database_name, file_path, collection_name, file_type):
                        print("\nGenerated query examples:")
                        for query in generate_query_examples(analysis, 'mongodb', collection_name):
                            print(f"\n{query}")

        elif choice == "3":
            file_path = input("Enter path to data file: ")
            file_type = input("Enter file type (csv/json): ").lower()
            validate_file(file_path, file_type)

        elif choice == "4":
            file_path = input("Enter path to data file: ")
            file_type = input("Enter file type (csv/json): ").lower()
            db_type = input("Enter database type (mysql/mongodb): ").lower()
            table_name = input("Enter table/collection name: ")
            
            analysis = validate_file(file_path, file_type)
            if analysis:
                print("\nGenerated query examples:")
                for query in generate_query_examples(analysis, db_type, table_name):
                    print(f"\n{query}")

        elif choice == "5":
            print("\nExiting database setup utility...")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    setup_database()
