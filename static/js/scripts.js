// Global utility functions
const ChatDB = {
    // Show loading spinner
    showLoading: function() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) spinner.classList.remove('d-none');
    },

    // Hide loading spinner
    hideLoading: function() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) spinner.classList.add('d-none');
    },

    // Show toast notification
    showToast: function(title, message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastTitle = document.getElementById('toast-title');
        const toastMessage = document.getElementById('toast-message');
        
        if (toast && toastTitle && toastMessage) {
            toastTitle.textContent = title;
            toastMessage.textContent = message;
            
            // Update icon based on type
            const icon = toast.querySelector('.fas');
            if (icon) {
                icon.className = `fas me-2 ${type === 'success' ? 'fa-check-circle text-success' : 
                                            type === 'error' ? 'fa-exclamation-circle text-danger' : 
                                            type === 'warning' ? 'fa-exclamation-triangle text-warning' : 
                                            'fa-info-circle text-info'}`;
            }
            
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    },

    // Format bytes to human readable
    formatBytes: function(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },

    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Database Connection
document.getElementById("connect-sql-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const dbUri = document.getElementById("sql-uri").value;

    if (!dbUri.trim()) {
        ChatDB.showToast('Error', 'Database URI is required', 'error');
        return;
    }

    ChatDB.showLoading();
    ChatDB.showToast('Connecting', 'Establishing database connection...', 'info');

    try {
        const res = await fetch("/connect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ db_uri: dbUri }),
        });
        const result = await res.json();

        const output = document.getElementById("connection-output");
        if (result.message) {
            output.innerHTML = `
                <div class="status-message status-success">
                    <i class="fas fa-check-circle me-2"></i>${result.message}
                </div>
            `;
            ChatDB.showToast('Success', 'Database connected successfully', 'success');
        } else {
            output.innerHTML = `
                <div class="status-message status-error">
                    <i class="fas fa-exclamation-circle me-2"></i>${result.error}
                </div>
            `;
            ChatDB.showToast('Connection Failed', result.error, 'error');
        }
    } catch (error) {
        ChatDB.showToast('Error', 'Failed to connect to database', 'error');
    } finally {
        ChatDB.hideLoading();
    }
});

// List SQL Tables
document.getElementById("list-sql-tables")?.addEventListener("click", async () => {
    ChatDB.showLoading();
    try {
        const res = await fetch("/api/tables");
        const result = await res.json();
        
        if (result.error) {
            ChatDB.showToast('Error', result.error, 'error');
        } else {
            const dataOutput = document.getElementById("data-output");
            let tablesInfo = 'Available Tables:\n\n';
            result.tables.forEach(table => {
                tablesInfo += `Table: ${table.name}\n`;
                tablesInfo += `Columns: ${table.columns.join(', ')}\n\n`;
            });
            dataOutput.innerHTML = `<pre>${tablesInfo}</pre>`;
            ChatDB.showToast('Tables Loaded', `Found ${result.tables.length} tables`, 'success');
        }
    } catch (error) {
        ChatDB.showToast('Error', 'Failed to load tables', 'error');
    } finally {
        ChatDB.hideLoading();
    }
});

// Execute Query with enhanced error handling
document.getElementById("query-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = document.getElementById("query").value.trim();

    if (!query) {
        ChatDB.showToast('Error', 'Please enter a query', 'error');
        return;
    }

    const startTime = performance.now();
    ChatDB.showLoading();
    ChatDB.showToast('Executing', 'Running your query...', 'info');

    try {
        const res = await fetch("/manage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
        });
        const result = await res.json();

        const endTime = performance.now();
        const executionTime = Math.round(endTime - startTime);

        // Clear previous output
        const dataOutput = document.getElementById("data-output");
        dataOutput.innerHTML = "";

        if (result.error) {
            // Add JSON Output title and display error
            const jsonTitle = document.createElement("h5");
            jsonTitle.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error Output:';
            dataOutput.appendChild(jsonTitle);

            const errorOutput = document.createElement("div");
            errorOutput.className = "status-message status-error";
            errorOutput.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${result.error}`;
            dataOutput.appendChild(errorOutput);

            ChatDB.showToast('Query Error', result.error, 'error');
        } else if (result.data) {
            // Add JSON Output title and display JSON
            const jsonTitle = document.createElement("h5");
            jsonTitle.innerHTML = '<i class="fas fa-code me-2"></i>JSON Output:';
            dataOutput.appendChild(jsonTitle);

            const jsonOutput = document.createElement("pre");
            jsonOutput.textContent = JSON.stringify(result.data, null, 2);
            dataOutput.appendChild(jsonOutput);

            // Add Tabular Output title and display table if data exists
            if (result.data && result.data.length > 0) {
                const tableTitle = document.createElement("h5");
                tableTitle.innerHTML = '<i class="fas fa-table me-2"></i>Tabular Output:';
                dataOutput.appendChild(tableTitle);

                const table = document.createElement("table");
                table.className = "table table-striped table-hover";
                table.style.borderRadius = "12px";
                table.style.overflow = "hidden";

                // Create table headers
                const headers = Object.keys(result.data[0]);
                const thead = document.createElement("thead");
                const headerRow = document.createElement("tr");

                headers.forEach((header) => {
                    const th = document.createElement("th");
                    th.textContent = header;
                    th.style.padding = "1rem";
                    th.style.fontWeight = "600";
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
                        td.style.padding = "1rem";
                        tr.appendChild(td);
                    });
                    tbody.appendChild(tr);
                });

                table.appendChild(tbody);
                dataOutput.appendChild(table);

                ChatDB.showToast('Query Success', `Executed in ${executionTime}ms - ${result.data.length} rows returned`, 'success');
            } else {
                const noDataMessage = document.createElement("div");
                noDataMessage.className = "alert alert-info";
                noDataMessage.innerHTML = '<i class="fas fa-info-circle me-2"></i>No data available or an error occurred.';
                dataOutput.appendChild(noDataMessage);
            }
        } else if (result.message) {
            const messageOutput = document.createElement("div");
            messageOutput.className = "status-message status-success";
            messageOutput.innerHTML = `<i class="fas fa-check-circle me-2"></i>${result.message}`;
            dataOutput.appendChild(messageOutput);
            
            ChatDB.showToast('Success', result.message, 'success');
        }
    } catch (error) {
        ChatDB.showToast('Error', 'Failed to execute query', 'error');
    } finally {
        ChatDB.hideLoading();
    }
});

// Enhanced Visualization
document.getElementById("visualize-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const chartContainer = document.getElementById('chart-container');
    const errorMessage = document.getElementById('error-message');
    
    const formData = {
        query: document.getElementById('query').value.trim(),
        x_axis: document.getElementById('x-axis').value.trim(),
        y_axis: document.getElementById('y-axis').value.trim(),
        chart_type: document.getElementById('chart-type').value
    };

    // Validate inputs
    if (!formData.query || !formData.x_axis || !formData.y_axis) {
        ChatDB.showToast('Error', 'Please fill in all required fields', 'error');
        return;
    }

    ChatDB.showLoading();
    ChatDB.showToast('Generating', 'Creating visualization...', 'info');

    try {
        const response = await fetch('/visualize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        
        if (result.error) {
            if (errorMessage) {
                errorMessage.textContent = result.error;
                errorMessage.classList.remove('d-none');
            }
            const chart = document.getElementById('chart');
            if (chart) chart.classList.add('d-none');
            ChatDB.showToast('Visualization Error', result.error, 'error');
        } else {
            if (errorMessage) errorMessage.classList.add('d-none');
            const chartImg = document.getElementById('chart');
            if (chartImg) {
                chartImg.src = `${result.plot_url}?t=${new Date().getTime()}`;
                chartImg.classList.remove('d-none');
            }
            ChatDB.showToast('Success', `Visualization created with ${result.data_points} data points`, 'success');
        }
    } catch (error) {
        if (errorMessage) {
            errorMessage.textContent = 'Error generating visualization';
            errorMessage.classList.remove('d-none');
        }
        const chart = document.getElementById('chart');
        if (chart) chart.classList.add('d-none');
        ChatDB.showToast('Error', 'Failed to generate visualization', 'error');
    } finally {
        ChatDB.hideLoading();
    }
});

// Enhanced Report Generation
document.getElementById("report-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = document.getElementById("report-data").value.trim();

    if (!data) {
        ChatDB.showToast('Error', 'Please provide data for the report', 'error');
        return;
    }

    let parsedData;
    try {
        parsedData = JSON.parse(data);
    } catch (error) {
        ChatDB.showToast('Error', 'Invalid JSON data provided', 'error');
        return;
    }

    ChatDB.showLoading();
    ChatDB.showToast('Generating', 'Creating report...', 'info');

    try {
        const res = await fetch("/report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: parsedData }),
        });
        const result = await res.json();
        
        if (result.report_url) {
            const link = document.getElementById("report-link");
            if (link) {
                link.href = result.report_url;
                link.classList.remove("d-none");
            }
            ChatDB.showToast('Success', `Report generated with ${result.row_count} rows and ${result.column_count} columns`, 'success');
        } else {
            ChatDB.showToast('Error', result.error || "Failed to generate report", 'error');
        }
    } catch (error) {
        ChatDB.showToast('Error', 'Failed to generate report', 'error');
    } finally {
        ChatDB.hideLoading();
    }
});

// File upload drag and drop functionality
document.addEventListener('DOMContentLoaded', function() {
    const fileUploadAreas = document.querySelectorAll('.file-upload-area');
    
    fileUploadAreas.forEach(area => {
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const fileInput = area.querySelector('input[type="file"]');
                if (fileInput) {
                    fileInput.files = files;
                    fileInput.dispatchEvent(new Event('change'));
                }
            }
        });
    });

    // Auto-save query drafts
    const queryInputs = document.querySelectorAll('textarea[id*="query"]');
    queryInputs.forEach(input => {
        const savedQuery = localStorage.getItem(`query-draft-${input.id}`);
        if (savedQuery) {
            input.value = savedQuery;
        }

        const saveDraft = ChatDB.debounce(() => {
            localStorage.setItem(`query-draft-${input.id}`, input.value);
        }, 1000);

        input.addEventListener('input', saveDraft);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter to execute query
        if (e.ctrlKey && e.key === 'Enter') {
            const executeBtn = document.querySelector('#execute-query');
            if (executeBtn) executeBtn.click();
        }
        
        // Ctrl+S to save (prevent default browser save)
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            ChatDB.showToast('Info', 'Use Ctrl+Enter to execute queries', 'info');
        }
    });
});

// Performance monitoring
window.addEventListener('load', function() {
    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
    console.log(`ChatDB loaded in ${loadTime}ms`);
    
    if (loadTime > 3000) {
        ChatDB.showToast('Performance', 'Page took longer than expected to load', 'warning');
    }
});

// Service Worker registration for PWA capabilities
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('SW registered: ', registration);
            })
            .catch(function(registrationError) {
                console.log('SW registration failed: ', registrationError);
            });
    });
}