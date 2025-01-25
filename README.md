# ChatDB

**ChatDB** is an interactive, web-based application that simplifies database management and visualization. With ChatDB, you can easily connect to a database, manage data, execute queries, generate reports, and visualize results using an intuitive interface.

[Explore ChatDB Online](https://chatdb-app-b12810368b1f.herokuapp.com/)

---

## Features

### 1. Connect to Databases
- Support for multiple database types, including:
  - SQLite
  - MySQL
  - PostgreSQL
- Easy-to-use connection interface with sample URI templates.

### 2. Manage Data
- **Upload Data**: Supports file uploads in CSV and JSON formats.
- **Execute Queries**: Run SQL queries directly from the interface and view tabular or JSON results.

### 3. Generate Reports
- Create downloadable reports based on provided JSON data.
- Outputs reports in CSV format for easy sharing and analysis.

### 4. Data Visualization
- Generate bar charts, line charts, and scatter plots based on SQL query results.
- Specify X-axis, Y-axis, and chart types for customized visualizations.

---

## Getting Started

### Prerequisites
- Python 3.8+
- A database system such as SQLite, MySQL, or PostgreSQL.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/DHYEY166/ChatDB.git
   cd ChatDB
   ```
2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser and navigate to `http://127.0.0.1:5000`.

---

## File Structure

- **app.py**: The main application logic.
- **templates/**: HTML templates for the web interface.
  - `base.html`: Base layout.
  - `index.html`: Homepage.
  - `connect.html`: Database connection page.
  - `manage.html`: Data management page.
  - `report.html`: Report generation page.
  - `visualize.html`: Data visualization page.
- **static/**: Static files (CSS, JavaScript, images).
  - `styles.css`: Custom styles.
  - `scripts.js`: JavaScript for interactivity.
- **requirements.txt**: List of dependencies.

---

## Usage Guide

### Homepage
Start by navigating to the homepage to access the main features of ChatDB.

### Connecting to a Database
1. Go to the "Connect" page.
2. Enter the database URI (e.g., `sqlite:///example.db` or `mysql+pymysql://user:password@localhost/dbname`).
3. Click "Connect" to establish the connection.

### Managing Data
- **Upload Files**: Upload CSV or JSON files for processing.
- **Run Queries**: Execute SQL queries and view the results in a table or JSON format.

### Generating Reports
1. Navigate to the "Reports" page.
2. Provide the data in JSON format.
3. Click "Generate Report" to download a CSV file.

### Visualizing Data
1. Go to the "Visualize" page.
2. Enter an SQL query and specify the X-axis, Y-axis, and chart type.
3. Generate the visualization and view the chart.

---

## Technologies Used
- **Frontend**: HTML, CSS, Bootstrap
- **Backend**: Python (Flask)
- **Database**: SQLite, MySQL, PostgreSQL
- **Visualization**: Custom charts rendered dynamically

---

## Contributing
1. Fork the repository.
2. Create a new branch for your feature:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add feature description"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-name
   ```
5. Open a Pull Request.

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

## Contact
For questions or suggestions, feel free to open an issue on the repository or contact the maintainer:
- **GitHub**: [DHYEY166](https://github.com/DHYEY166)

