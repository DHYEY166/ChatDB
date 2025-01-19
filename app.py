import streamlit as st
import pandas as pd
import importlib.util
import os

# Load the uploaded files dynamically
def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Paths to uploaded files
chatdb_path = "chatDB.py"
database_setup_path = "database_setup.py"

# Load modules
if os.path.exists(chatdb_path):
    chatDB = load_module_from_path("chatDB", chatdb_path)
else:
    st.error("chatDB.py not found!")

if os.path.exists(database_setup_path):
    database_setup = load_module_from_path("database_setup", database_setup_path)
else:
    st.error("database_setup.py not found!")

# Streamlit App
st.title("ChatDB Application")

menu_options = [
    "Connect to SQL Database",
    "Connect to NoSQL Database",
    "List tables/collections",
    "View sample data",
    "Execute natural language query",
    "Execute custom query",
    "Visualize data",
    "Get query suggestions",
    "Generate database report",
    "Exit",
]

selected_option = st.sidebar.selectbox("ChatDB Menu", menu_options)

# Functions for each task
def connect_to_sql():
    st.subheader("Connect to SQL Database")
    connection_string = st.text_input("Enter SQL connection string:")
    if st.button("Connect"):
        try:
            conn = database_setup.connect_to_sql(connection_string)
            st.success("Connected to SQL database!")
            return conn
        except Exception as e:
            st.error(f"Error connecting to SQL database: {e}")

def connect_to_nosql():
    st.subheader("Connect to NoSQL Database")
    connection_details = st.text_input("Enter NoSQL connection details:")
    if st.button("Connect"):
        try:
            conn = database_setup.connect_to_nosql(connection_details)
            st.success("Connected to NoSQL database!")
            return conn
        except Exception as e:
            st.error(f"Error connecting to NoSQL database: {e}")

def list_tables(conn):
    st.subheader("List Tables/Collections")
    try:
        tables = chatDB.list_tables(conn)
        st.write(tables)
    except Exception as e:
        st.error(f"Error listing tables: {e}")

def view_sample_data(conn):
    st.subheader("View Sample Data")
    table_name = st.text_input("Enter table/collection name:")
    if st.button("View"):
        try:
            sample_data = chatDB.view_sample_data(conn, table_name)
            st.write(sample_data)
        except Exception as e:
            st.error(f"Error viewing sample data: {e}")

def execute_nl_query(conn):
    st.subheader("Execute Natural Language Query")
    query = st.text_area("Enter natural language query:")
    if st.button("Run Query"):
        try:
            result = chatDB.execute_nl_query(conn, query)
            st.write(result)
        except Exception as e:
            st.error(f"Error executing query: {e}")

def execute_custom_query(conn):
    st.subheader("Execute Custom Query")
    query = st.text_area("Enter SQL/NoSQL query:")
    if st.button("Run Query"):
        try:
            result = chatDB.execute_custom_query(conn, query)
            st.write(result)
        except Exception as e:
            st.error(f"Error executing query: {e}")

def visualize_data(conn):
    st.subheader("Visualize Data")
    table_name = st.text_input("Enter table/collection name:")
    if st.button("Visualize"):
        try:
            data = chatDB.view_sample_data(conn, table_name)
            df = pd.DataFrame(data)
            st.line_chart(df)  # You can use other visualizations like st.bar_chart
        except Exception as e:
            st.error(f"Error visualizing data: {e}")

def get_query_suggestions():
    st.subheader("Get Query Suggestions")
    query_context = st.text_area("Describe the query context:")
    if st.button("Get Suggestions"):
        try:
            suggestions = chatDB.get_query_suggestions(query_context)
            st.write(suggestions)
        except Exception as e:
            st.error(f"Error getting suggestions: {e}")

def generate_report(conn):
    st.subheader("Generate Database Report")
    if st.button("Generate"):
        try:
            report = chatDB.generate_report(conn)
            st.download_button("Download Report", report, "database_report.txt")
        except Exception as e:
            st.error(f"Error generating report: {e}")

# Main application logic
if selected_option == "Connect to SQL Database":
    conn = connect_to_sql()
elif selected_option == "Connect to NoSQL Database":
    conn = connect_to_nosql()
elif selected_option == "List tables/collections":
    list_tables(conn)
elif selected_option == "View sample data":
    view_sample_data(conn)
elif selected_option == "Execute natural language query":
    execute_nl_query(conn)
elif selected_option == "Execute custom query":
    execute_custom_query(conn)
elif selected_option == "Visualize data":
    visualize_data(conn)
elif selected_option == "Get query suggestions":
    get_query_suggestions()
elif selected_option == "Generate database report":
    generate_report(conn)
elif selected_option == "Exit":
    st.info("Thank you for using ChatDB!")
