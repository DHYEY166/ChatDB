// Connect to SQL Database
document.getElementById("connect-sql-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const dbUri = document.getElementById("sql-uri").value;

    try {
        const res = await fetch("/connect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ db_type: "sql", db_uri: dbUri }),
        });
        const result = await res.json();

        const output = document.getElementById("connection-output");
        if (result.message) {
            output.textContent = `Success: ${result.message}`;
            output.style.color = "green";
        } else {
            output.textContent = `Error: ${result.error}`;
            output.style.color = "red";
        }
    } catch (error) {
        alert("An error occurred while connecting to the SQL database.");
    }
});

// List SQL Tables
document.getElementById("list-sql-tables")?.addEventListener("click", async () => {
    try {
        const res = await fetch("/manage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ db_type: "sql" }),
        });
        const result = await res.json();
        document.getElementById("data-output").textContent = JSON.stringify(result.tables || result.error, null, 2);
    } catch (error) {
        alert("An error occurred while listing SQL tables.");
    }
});

// Execute Query
document.getElementById("query-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("query").value;

    const payload = { db_type: "sql", query };

    try {
        const res = await fetch("/manage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const result = await res.json();

        // Clear previous output
        const dataOutput = document.getElementById("data-output");
        dataOutput.innerHTML = "";

        // Add JSON Output title and display JSON
        const jsonTitle = document.createElement("h5");
        jsonTitle.textContent = "JSON Output:";
        dataOutput.appendChild(jsonTitle);

        const jsonOutput = document.createElement("pre");
        jsonOutput.textContent = JSON.stringify(result.data, null, 2);
        dataOutput.appendChild(jsonOutput);

        // Add Tabular Output title and display table if data exists
        if (result.data && result.data.length > 0) {
            const tableTitle = document.createElement("h5");
            tableTitle.textContent = "Tabular Output:";
            dataOutput.appendChild(tableTitle);

            const table = document.createElement("table");
            table.border = "1";
            table.style.borderCollapse = "collapse";
            table.style.width = "100%";

            // Create table headers
            const headers = Object.keys(result.data[0]);
            const thead = document.createElement("thead");
            const headerRow = document.createElement("tr");

            headers.forEach((header) => {
                const th = document.createElement("th");
                th.textContent = header;
                th.style.border = "1px solid black";
                th.style.padding = "8px";
                th.style.textAlign = "left";
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create table rows
            const tbody = document.createElement("tbody");
            result.data.forEach((row) => {
                const tr = document.createElement("tr");
                headers.forEach((header) => {
                    const td = document.createElement("td");
                    td.textContent = row[header];
                    td.style.border = "1px solid black";
                    td.style.padding = "8px";
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });

            table.appendChild(tbody);
            dataOutput.appendChild(table);
        } else {
            const noDataMessage = document.createElement("p");
            noDataMessage.textContent = "No data available or an error occurred.";
            dataOutput.appendChild(noDataMessage);
        }
    } catch (error) {
        alert("An error occurred while executing the query.");
    }
});

// Generate Visualization
document.getElementById("visualize-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const chartContainer = document.getElementById('chart-container');
    const errorMessage = document.getElementById('error-message');
    
    const formData = {
        query: document.getElementById('query').value,
        x_axis: document.getElementById('x-axis').value,
        y_axis: document.getElementById('y-axis').value,
        chart_type: document.getElementById('chart-type').value
    };

    try {
        const response = await fetch('/visualize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        
        if (result.error) {
            errorMessage.textContent = result.error;
            errorMessage.classList.remove('d-none');
            document.getElementById('chart').classList.add('d-none');
        } else {
            errorMessage.classList.add('d-none');
            const chartImg = document.getElementById('chart');
            chartImg.src = `${result.plot_url}?t=${new Date().getTime()}`;
            chartImg.classList.remove('d-none');
        }
    } catch (error) {
        errorMessage.textContent = 'Error generating visualization';
        errorMessage.classList.remove('d-none');
        document.getElementById('chart').classList.add('d-none');
    }
});

// Generate Report
document.getElementById("report-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = document.getElementById("report-data").value;

    try {
        const res = await fetch("/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: JSON.parse(data) }),
        });
        const result = await res.json();
        if (result.report_url) {
            const link = document.getElementById("report-link");
            link.href = result.report_url;
            link.classList.remove("d-none");
        } else {
            alert(result.error || "An error occurred while generating the report.");
        }
    } catch (error) {
        alert("Invalid JSON data provided for the report.");
    }
});