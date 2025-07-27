// Global utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showLoading(element) {
    element.disabled = true;
    element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
}

function hideLoading(element, originalText) {
    element.disabled = false;
    element.innerHTML = originalText;
}

function formatData(data) {
    if (Array.isArray(data)) {
        return data.map(item => {
            if (typeof item === 'object') {
                return Object.entries(item).map(([key, value]) => 
                    `${key}: ${JSON.stringify(value)}`
                ).join(', ');
            }
            return String(item);
        }).join('\n');
    }
    return JSON.stringify(data, null, 2);
}

// Connect to SQL Database
document.getElementById("connect-sql-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    showLoading(submitBtn);
    
    const dbUri = document.getElementById("sql-uri").value.trim();

    try {
        const res = await fetch("/connect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ db_uri: dbUri }),
        });
        
        const result = await res.json();

        const output = document.getElementById("connection-output");
        if (result.message) {
            output.innerHTML = `<div class="alert alert-success">✅ ${result.message}</div>`;
            showAlert('Database connected successfully!', 'success');
        } else {
            output.innerHTML = `<div class="alert alert-danger">❌ ${result.error}</div>`;
            showAlert(result.error, 'danger');
        }
    } catch (error) {
        console.error('Connection error:', error);
        showAlert('An error occurred while connecting to the database.', 'danger');
    } finally {
        hideLoading(submitBtn, originalText);
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

// Execute Query with enhanced error handling
document.getElementById("query-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    showLoading(submitBtn);
    
    const query = document.getElementById("query").value.trim();
    
    if (!query) {
        showAlert('Please enter a query.', 'warning');
        hideLoading(submitBtn, originalText);
        return;
    }

    try {
        const res = await fetch("/manage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
        });
        
        const result = await res.json();

        // Clear previous output
        const dataOutput = document.getElementById("data-output");
        dataOutput.innerHTML = "";

        if (result.error) {
            dataOutput.innerHTML = `<div class="alert alert-danger">❌ ${result.error}</div>`;
            showAlert(result.error, 'danger');
        } else if (result.data) {
            // Add success message
            const successMsg = document.createElement("div");
            successMsg.className = "alert alert-success mb-3";
            successMsg.innerHTML = `✅ Query executed successfully! Found ${result.row_count || 0} rows and ${result.column_count || 0} columns.`;
            dataOutput.appendChild(successMsg);

            // Add JSON Output
            const jsonTitle = document.createElement("h5");
            jsonTitle.textContent = "JSON Output:";
            jsonTitle.className = "mt-3 mb-2";
            dataOutput.appendChild(jsonTitle);

            const jsonOutput = document.createElement("pre");
            jsonOutput.textContent = JSON.stringify(result.data, null, 2);
            dataOutput.appendChild(jsonOutput);

            // Add Tabular Output if data exists
            if (result.data && result.data.length > 0) {
                const tableTitle = document.createElement("h5");
                tableTitle.textContent = "Tabular Output:";
                tableTitle.className = "mt-4 mb-2";
                dataOutput.appendChild(tableTitle);

                const table = document.createElement("table");
                table.className = "table table-striped table-hover";
                table.style.width = "100%";

                // Create table headers
                const headers = Object.keys(result.data[0]);
                const thead = document.createElement("thead");
                const headerRow = document.createElement("tr");

                headers.forEach((header) => {
                    const th = document.createElement("th");
                    th.textContent = header;
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
                        td.textContent = row[header] !== null ? row[header] : '';
                        tr.appendChild(td);
                    });
                    tbody.appendChild(tr);
                });

                table.appendChild(tbody);
                dataOutput.appendChild(table);
            }
            
            showAlert('Query executed successfully!', 'success');
        } else if (result.message) {
            dataOutput.innerHTML = `<div class="alert alert-info">ℹ️ ${result.message}</div>`;
            showAlert(result.message, 'info');
        }
    } catch (error) {
        console.error('Query execution error:', error);
        showAlert('An error occurred while executing the query.', 'danger');
    } finally {
        hideLoading(submitBtn, originalText);
    }
});

// File Upload with progress indication
document.getElementById("upload-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    const fileInput = document.getElementById("file");
    const fileTypeSelect = document.getElementById("file-type");
    
    if (!fileInput.files[0]) {
        showAlert('Please select a file to upload.', 'warning');
        return;
    }
    
    showLoading(submitBtn);
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('file_type', fileTypeSelect.value);

    try {
        const res = await fetch("/upload", {
            method: "POST",
            body: formData,
        });
        
        const result = await res.json();

        if (result.error) {
            showAlert(result.error, 'danger');
        } else {
            showAlert(`File uploaded successfully! Table: ${result.table_name}, Rows: ${result.row_count}`, 'success');
            
            // Clear file input
            fileInput.value = '';
        }
    } catch (error) {
        console.error('Upload error:', error);
        showAlert('An error occurred while uploading the file.', 'danger');
    } finally {
        hideLoading(submitBtn, originalText);
    }
});

// Generate Visualization with enhanced UI
document.getElementById("visualize-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    showLoading(submitBtn);
    
    const chartContainer = document.getElementById('chart-container');
    const errorMessage = document.getElementById('error-message');
    const chartImg = document.getElementById('chart');
    
    // Hide previous results
    errorMessage.classList.add('d-none');
    chartImg.classList.add('d-none');
    
    const formData = {
        query: document.getElementById('query').value.trim(),
        x_axis: document.getElementById('x-axis').value.trim(),
        y_axis: document.getElementById('y-axis').value.trim(),
        chart_type: document.getElementById('chart-type').value
    };

    // Validation
    if (!formData.query || !formData.x_axis || !formData.y_axis) {
        showAlert('Please fill in all required fields.', 'warning');
        hideLoading(submitBtn, originalText);
        return;
    }

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
            showAlert(result.error, 'danger');
        } else {
            chartImg.src = `${result.plot_url}?t=${new Date().getTime()}`;
            chartImg.classList.remove('d-none');
            showAlert(`Visualization created successfully! Data points: ${result.data_points}`, 'success');
        }
    } catch (error) {
        console.error('Visualization error:', error);
        errorMessage.textContent = 'Error generating visualization';
        errorMessage.classList.remove('d-none');
        showAlert('Error generating visualization', 'danger');
    } finally {
        hideLoading(submitBtn, originalText);
    }
});

// Generate Report with validation
document.getElementById("report-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    showLoading(submitBtn);
    
    const dataInput = document.getElementById("report-data");
    const data = dataInput.value.trim();

    if (!data) {
        showAlert('Please provide data for the report.', 'warning');
        hideLoading(submitBtn, originalText);
        return;
    }

    try {
        // Validate JSON
        const parsedData = JSON.parse(data);
        
        const res = await fetch("/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: parsedData }),
        });
        
        const result = await res.json();
        
        if (result.error) {
            showAlert(result.error, 'danger');
        } else {
            const link = document.getElementById("report-link");
            link.href = result.report_url;
            link.classList.remove("d-none");
            showAlert(`Report generated successfully! Rows: ${result.row_count}, Columns: ${result.column_count}`, 'success');
        }
    } catch (error) {
        if (error instanceof SyntaxError) {
            showAlert('Invalid JSON data provided for the report.', 'danger');
        } else {
            console.error('Report generation error:', error);
            showAlert('An error occurred while generating the report.', 'danger');
        }
    } finally {
        hideLoading(submitBtn, originalText);
    }
});

// Auto-resize textareas
document.querySelectorAll('textarea').forEach(textarea => {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
});

// Add fade-in animation to cards
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Copy to clipboard functionality
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard!', 'success');
    }).catch(() => {
        showAlert('Failed to copy to clipboard', 'danger');
    });
}

// Add copy buttons to code blocks
document.addEventListener('DOMContentLoaded', function() {
    const codeBlocks = document.querySelectorAll('pre');
    codeBlocks.forEach(block => {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-sm btn-outline-secondary position-absolute';
        copyBtn.style.top = '10px';
        copyBtn.style.right = '10px';
        copyBtn.innerHTML = '📋 Copy';
        copyBtn.onclick = () => copyToClipboard(block.textContent);
        
        block.style.position = 'relative';
        block.appendChild(copyBtn);
    });
});