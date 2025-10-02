// MTG Village Web Application - Frontend JavaScript
// Adapted for Vercel Serverless Functions

// Configuration - Update this with your Vercel app URL after deployment
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:3000' 
    : 'https://mtgvillage.vercel.app';

// Global variables
let availableStores = [];
let currentResults = [];
let currentTable = null;
let progressInterval = null;
let progressValue = 0;

// Initialize application when document is ready
$(document).ready(function() {
    console.log('MTG Village Web App loaded');
    console.log('API Base URL:', API_BASE_URL);
    
    // Show API URL notice if not configured
    if (API_BASE_URL.includes('YOUR_VERCEL_APP_URL_HERE')) {
        showApiUrlNotice();
    }
    
    // Load available stores
    loadStores();
    
    // Set up event handlers
    setupEventHandlers();
    
    // Update card count on input
    updateCardCount();
});

// Show notice about API URL configuration
function showApiUrlNotice() {
    const notice = `
        <div class="alert alert-warning alert-dismissible fade show" role="alert">
            <i class="fas fa-info-circle"></i>
            <strong>Configuration needed:</strong> Please update the API_BASE_URL in assets/js/app.js with your Vercel app URL.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('.container-fluid').prepend(notice);
}

// Load available stores from API
async function loadStores() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stores`);
        const data = await response.json();
        
        if (data.success) {
            availableStores = data.stores;
            renderStoreSelection();
        } else {
            showError('Failed to load stores: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading stores:', error);
        showError('Failed to connect to server. Please check if the API URL is configured correctly.');
    }
}

// Render store selection checkboxes
function renderStoreSelection() {
    const container = $('#storeSelection');
    
    if (availableStores.length === 0) {
        container.html(`
            <div class="text-center text-muted">
                <i class="fas fa-exclamation-triangle"></i>
                No stores configured
            </div>
        `);
        return;
    }
    
    let html = '';
    availableStores.forEach(store => {
        html += `
            <div class="form-check mb-2">
                <input class="form-check-input store-checkbox" type="checkbox" 
                       value="${store.key}" id="store_${store.key}" checked>
                <label class="form-check-label" for="store_${store.key}">
                    <strong>${store.name}</strong>
                    <small class="text-muted d-block">${store.type}</small>
                </label>
            </div>
        `;
    });
    
    container.html(html);
}

// Set up event handlers
function setupEventHandlers() {
    // Form submission
    $('#priceCheckForm').on('submit', function(e) {
        e.preventDefault();
        checkPrices();
    });
    
    // Card input monitoring
    $('#cardNames').on('input', updateCardCount);
    
    // Store selection buttons
    $('#selectAllStores').on('click', function() {
        $('.store-checkbox').prop('checked', true);
    });
    
    $('#selectNoStores').on('click', function() {
        $('.store-checkbox').prop('checked', false);
    });
    
    // CSV export
    $('#exportCsvBtn').on('click', exportToCsv);
}

// Normalize card input into clean card name list
function parseCardInput(text) {
    return text
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(line => {
            const quantityMatch = line.match(/^(\d+)\s+(.*)$/);
            if (quantityMatch) {
                const name = quantityMatch[2].trim();
                return name.length > 0 ? name : line;
            }
            return line;
        });
}

function resetProgressBar() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    progressValue = 0;
    const $bar = $('#loadingProgressBar');
    $bar.removeClass('bg-success bg-danger');
    if (!$bar.hasClass('progress-bar-animated')) {
        $bar.addClass('progress-bar-animated');
    }
    $bar.css('width', '0%').attr('aria-valuenow', 0).text('0%');
    $('#loadingProgressText').text('');
}

function startProgressBar(cardCount) {
    resetProgressBar();
    const total = Math.max(cardCount, 1);
    const step = Math.max(2, Math.floor(70 / total));
    const interval = Math.max(250, Math.min(800, total * 150));
    $('#loadingProgressText').text(`Checking ${total} card${total !== 1 ? 's' : ''}...`);
    progressInterval = setInterval(() => {
        if (progressValue < 90) {
            progressValue = Math.min(90, progressValue + step);
            updateProgressBar(progressValue);
        } else {
            progressValue = Math.min(95, progressValue + 1);
            updateProgressBar(progressValue);
        }
    }, interval);
}

function updateProgressBar(value, label) {
    const clamped = Math.max(0, Math.min(100, Math.round(value)));
    const $bar = $('#loadingProgressBar');
    $bar.css('width', `${clamped}%`).attr('aria-valuenow', clamped).text(`${clamped}%`);
    if (label) {
        $('#loadingProgressText').text(label);
    }
}

function completeProgressBar(message = 'Completed') {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    const $bar = $('#loadingProgressBar');
    $bar.removeClass('progress-bar-animated bg-danger').addClass('bg-success');
    progressValue = 100;
    updateProgressBar(progressValue, message);
}

function failProgressBar(message = 'Failed') {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    const $bar = $('#loadingProgressBar');
    $bar.removeClass('progress-bar-animated bg-success').addClass('bg-danger');
    progressValue = 100;
    updateProgressBar(progressValue, message);
}

// Update card count display
function updateCardCount() {
    const text = $('#cardNames').val();
    const lines = parseCardInput(text);
    $('#cardCount').text(lines.length);
}

// Get selected stores
function getSelectedStores() {
    const selected = [];
    $('.store-checkbox:checked').each(function() {
        selected.push($(this).val());
    });
    return selected;
}

// Main price checking function
async function checkPrices() {
    const rawCardText = $('#cardNames').val();
    const normalizedCards = parseCardInput(rawCardText);
    const cardText = normalizedCards.join('\n');
    const selectedStores = getSelectedStores();
    
    // Validation
    if (normalizedCards.length === 0) {
        showError('Please enter some card names');
        return;
    }
    
    if (selectedStores.length === 0) {
        showError('Please select at least one store');
        return;
    }
    
    // Show loading state
    showLoading();
    startProgressBar(normalizedCards.length);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/check-prices`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cards: cardText,
                stores: selectedStores
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            completeProgressBar('Finished');
            currentResults = data.results;
            displayResults(data.results, data.summary, data.selected_stores);
        } else {
            failProgressBar('Request failed');
            showError(data.error);
        }
    } catch (error) {
        console.error('Error checking prices:', error);
        failProgressBar('Request failed');
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            showError('Failed to connect to API. Please check your internet connection and API configuration.');
        } else {
            showError('Failed to check prices. Please try again.');
        }
    }
}

// Display results in table
function displayResults(results, summary, selectedStores) {
    hideAllStates();
    $('#resultsSection').removeClass('d-none');
    
    // Display summary
    displaySummary(summary);
    
    // Build table headers
    const headers = ['Card Name'];
    selectedStores.forEach(storeKey => {
        const store = availableStores.find(s => s.key === storeKey);
        headers.push(store ? store.name : storeKey);
    });
    headers.push('Lowest Price', 'Best Store');
    
    // Build table HTML
    let headerHtml = '';
    headers.forEach(header => {
        headerHtml += `<th>${header}</th>`;
    });
    $('#tableHeaders').html(headerHtml);
    
    // Build table body
    let bodyHtml = '';
    results.forEach(result => {
        let rowHtml = '<tr>';
        
        // Card name
        rowHtml += `<td><strong>${escapeHtml(result.card_name)}</strong></td>`;
        
        // Store prices
        selectedStores.forEach(storeKey => {
            const price = result[`${storeKey}_price`];
            const availability = result[`${storeKey}_availability`];
            
            if (price === 'n/a') {
                rowHtml += `<td><span class="text-muted">n/a</span></td>`;
            } else {
                const badgeClass = availability === 'Available' ? 'bg-success' : 'bg-secondary';
                rowHtml += `
                    <td>
                        <span class="fw-bold">$${parseFloat(price).toFixed(2)}</span>
                        <br>
                        <small><span class="badge ${badgeClass}">${availability}</span></small>
                    </td>
                `;
            }
        });
        
        // Lowest price
        const lowestPrice = result.lowest_price;
        if (lowestPrice === 'n/a') {
            rowHtml += `<td><span class="text-muted">n/a</span></td>`;
        } else {
            rowHtml += `<td><strong class="text-success">$${parseFloat(lowestPrice).toFixed(2)}</strong></td>`;
        }
        
        // Best store
        const bestStore = result.lowest_price_store;
        if (bestStore === 'n/a') {
            rowHtml += `<td><span class="text-muted">n/a</span></td>`;
        } else {
            const store = availableStores.find(s => s.key === bestStore);
            rowHtml += `<td><span class="badge bg-primary">${store ? store.name : bestStore}</span></td>`;
        }
        
        rowHtml += '</tr>';
        bodyHtml += rowHtml;
    });
    $('#tableBody').html(bodyHtml);
    
    // Initialize or reinitialize DataTable
    if (currentTable) {
        currentTable.destroy();
    }
    
    currentTable = $('#resultsTable').DataTable({
        responsive: true,
        pageLength: 25,
        order: [[0, 'asc']], // Sort by card name initially
        columnDefs: [
            {
                targets: '_all',
                className: 'align-middle'
            }
        ],
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
             '<"row"<"col-sm-12"tr>>' +
             '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
        language: {
            search: 'Filter results:',
            lengthMenu: 'Show _MENU_ cards per page',
            info: 'Showing _START_ to _END_ of _TOTAL_ cards',
            emptyTable: 'No cards found',
            zeroRecords: 'No matching cards found'
        }
    });
}

// Display summary information
function displaySummary(summary) {
    let html = `
        <div class="row">
            <div class="col-md-4">
                <div class="text-center">
                    <h4 class="text-primary">${summary.total_cards}</h4>
                    <small class="text-muted">Total Cards</small>
                </div>
            </div>
            <div class="col-md-4">
                <div class="text-center">
                    <h4 class="text-success">$${summary.overall_lowest_total.toFixed(2)}</h4>
                    <small class="text-muted">Overall Lowest Total</small>
                </div>
            </div>
            <div class="col-md-4">
                <div class="text-center">
                    <h4 class="text-info">${Object.keys(summary.store_stats).length}</h4>
                    <small class="text-muted">Stores Checked</small>
                </div>
            </div>
        </div>
    `;
    
    // Per-store statistics
    if (Object.keys(summary.store_stats).length > 0) {
        html += `
            <hr class="my-3">
            <h6>Per-Store Statistics:</h6>
            <div class="row">
        `;
        
        Object.entries(summary.store_stats).forEach(([storeKey, stats]) => {
            html += `
                <div class="col-md-6 col-lg-4 mb-2">
                    <div class="border rounded p-2">
                        <strong>${stats.name}</strong><br>
                        <small class="text-muted">
                            ${stats.available} available • $${stats.total_price.toFixed(2)} total
                        </small>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    $('#summaryContent').html(html);
}

// Export results to CSV
function exportToCsv() {
    if (!currentResults || currentResults.length === 0) {
        showError('No results to export');
        return;
    }
    
    // Get selected stores for proper column order
    const selectedStores = getSelectedStores();
    
    // Build CSV headers
    const headers = ['Card Name'];
    selectedStores.forEach(storeKey => {
        const store = availableStores.find(s => s.key === storeKey);
        const storeName = store ? store.name : storeKey;
        headers.push(`${storeName} Price`, `${storeName} Availability`);
    });
    headers.push('Lowest Price', 'Best Store');
    
    // Build CSV content
    let csvContent = headers.join(',') + '\n';
    
    currentResults.forEach(result => {
        const row = [];
        
        // Card name (escape quotes)
        row.push(`"${result.card_name.replace(/"/g, '""')}"`);
        
        // Store data
        selectedStores.forEach(storeKey => {
            const price = result[`${storeKey}_price`];
            const availability = result[`${storeKey}_availability`];
            row.push(price);
            row.push(`"${availability}"`);
        });
        
        // Lowest price and best store
        row.push(result.lowest_price);
        row.push(`"${result.lowest_price_store}"`);
        
        csvContent += row.join(',') + '\n';
    });
    
    // Create download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `mtg_prices_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// UI state management functions
function showLoading() {
    hideAllStates();
    $('#loadingState').removeClass('d-none');
    resetProgressBar();
}

function showError(message) {
    hideAllStates();
    $('#errorMessage').text(message);
    $('#errorState').removeClass('d-none');
}

function hideAllStates() {
    $('#welcomeState, #loadingState, #errorState, #resultsSection').addClass('d-none');
}

// Utility function to escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Console log for debugging
console.log('MTG Village app.js loaded successfully');
console.log('Remember to update API_BASE_URL after Vercel deployment!');
