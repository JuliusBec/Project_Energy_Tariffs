const API_BASE_URL = 'http://localhost:8000';

// Function to handle CSV file upload
async function handleCSVUpload(file, householdSize = 2) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('household_size', householdSize);

    try {
        const response = await fetch(`${API_BASE_URL}/api/calculate-with-csv`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();
        displayResults(data.results, 'CSV Data');
        return data;
    } catch (error) {
        console.error('Error uploading CSV:', error);
        showError(`Error processing file: ${error.message}`);
        throw error;
    }
}

// Function to calculate with basic data (no smart meter)
async function calculateBasic(userData) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/calculate-basic`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Calculation failed');
        }

        const data = await response.json();
        displayResults(data.results, 'Estimated Data');
        return data;
    } catch (error) {
        console.error('Error calculating basic:', error);
        showError(`Error calculating costs: ${error.message}`);
        throw error;
    }
}

// Function to get available tariffs
async function getAvailableTariffs() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/tariffs`);
        const data = await response.json();
        return data.tariffs;
    } catch (error) {
        console.error('Error fetching tariffs:', error);
        return [];
    }
}

// Function to get backtest data
async function getBacktestData(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/api/backtest-data`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to generate backtest data');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching backtest data:', error);
        showError(`Error generating backtest: ${error.message}`);
        throw error;
    }
}

// Function to display results in HTML
function displayResults(results, dataSource) {
    const resultsContainer = document.getElementById('results-container');
    
    if (!resultsContainer) {
        console.error('Results container not found');
        return;
    }

    // Clear previous results
    resultsContainer.innerHTML = '';

    // Create results HTML
    const resultsHTML = `
        <div class="results-section">
            <h3>Tariff Comparison Results (${dataSource})</h3>
            <div class="tariff-grid">
                ${results.map(tariff => `
                    <div class="tariff-card ${tariff.tariff_type}">
                        <h4>${tariff.tariff_name}</h4>
                        <p class="tariff-type">${tariff.tariff_type.toUpperCase()}</p>
                        <div class="cost-info">
                            <p><strong>Monthly Cost:</strong> €${tariff.monthly_cost.toFixed(2)}</p>
                            <p><strong>Annual Cost:</strong> €${tariff.annual_cost.toFixed(2)}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    resultsContainer.innerHTML = resultsHTML;
}

// Function to show error messages
function showError(message) {
    const errorContainer = document.getElementById('error-container') || 
                          document.createElement('div');
    
    errorContainer.id = 'error-container';
    errorContainer.className = 'error-message';
    errorContainer.innerHTML = `
        <div class="alert alert-error">
            <span class="close-btn" onclick="this.parentElement.parentElement.style.display='none'">&times;</span>
            ${message}
        </div>
    `;
    
    // Insert at the top of the main content
    const mainContent = document.querySelector('main') || document.body;
    mainContent.insertBefore(errorContainer, mainContent.firstChild);
}