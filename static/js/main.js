/**
 * Vigilance File Management System - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sortable tables
    initSortableTables();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.forEach(function(popoverTriggerEl) {
        new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Search autocomplete for file numbers
    var fileSearchInput = document.getElementById('file_number_search');
    if (fileSearchInput) {
        fileSearchInput.addEventListener('input', debounce(function(e) {
            var query = e.target.value;
            if (query.length >= 2) {
                searchFiles(query);
            }
        }, 300));
    }

    // Employee PEN lookup
    var penInput = document.getElementById('pen');
    if (penInput) {
        penInput.addEventListener('blur', function(e) {
            var pen = e.target.value.trim();
            if (pen) {
                fetchEmployeeDetails(pen);
            }
        });
    }

    // Institution autocomplete
    var institutionInput = document.getElementById('institution_name');
    if (institutionInput) {
        institutionInput.addEventListener('input', debounce(function(e) {
            var query = e.target.value;
            if (query.length >= 2) {
                searchInstitutions(query);
            }
        }, 300));
    }

    // Print button
    var printButtons = document.querySelectorAll('[data-print]');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Date input formatting
    var dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        // Set max date to today for certain date fields
        if (input.dataset.maxToday) {
            input.max = new Date().toISOString().split('T')[0];
        }
    });

    // Character counter for textareas
    var textareas = document.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(function(textarea) {
        var maxLength = parseInt(textarea.dataset.maxLength);
        var counter = document.createElement('small');
        counter.className = 'text-muted float-end';
        updateCounter();
        
        textarea.parentNode.appendChild(counter);
        textarea.addEventListener('input', updateCounter);
        
        function updateCounter() {
            var remaining = maxLength - textarea.value.length;
            counter.textContent = remaining + ' characters remaining';
            if (remaining < 50) {
                counter.className = 'text-warning float-end';
            }
            if (remaining < 0) {
                counter.className = 'text-danger float-end';
            }
        }
    });
});

// Debounce function
function debounce(func, wait) {
    var timeout;
    return function executedFunction() {
        var context = this;
        var args = arguments;
        var later = function() {
            timeout = null;
            func.apply(context, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search files API
function searchFiles(query) {
    fetch('/files/api/search?q=' + encodeURIComponent(query))
        .then(function(response) { return response.json(); })
        .then(function(data) {
            displaySearchResults(data);
        })
        .catch(function(error) {
            console.error('Error searching files:', error);
        });
}

// Display search results
function displaySearchResults(results) {
    var dropdown = document.getElementById('search-results-dropdown');
    if (!dropdown) return;
    
    dropdown.innerHTML = '';
    
    if (results.length === 0) {
        dropdown.innerHTML = '<div class="dropdown-item text-muted">No results found</div>';
    } else {
        results.forEach(function(file) {
            var item = document.createElement('a');
            item.className = 'dropdown-item';
            item.href = '/files/' + file.file_number;
            item.textContent = file.file_number + ' - ' + (file.subject || 'No subject');
            dropdown.appendChild(item);
        });
    }
    
    dropdown.style.display = 'block';
}

// Fetch employee details by PEN
function fetchEmployeeDetails(pen) {
    fetch('/employees/api/get/' + encodeURIComponent(pen))
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.found) {
                // Fill form fields
                var nameInput = document.getElementById('employee_name');
                var designationInput = document.getElementById('designation');
                var institutionInput = document.getElementById('institution');
                
                if (nameInput) nameInput.value = data.name || '';
                if (designationInput) designationInput.value = data.designation || '';
                if (institutionInput) institutionInput.value = data.institution_name || '';
            }
        })
        .catch(function(error) {
            console.error('Error fetching employee details:', error);
        });
}

// Search institutions
function searchInstitutions(query) {
    fetch('/institutions/api/search?q=' + encodeURIComponent(query))
        .then(function(response) { return response.json(); })
        .then(function(data) {
            displayInstitutionResults(data);
        })
        .catch(function(error) {
            console.error('Error searching institutions:', error);
        });
}

// Display institution search results
function displayInstitutionResults(results) {
    var datalist = document.getElementById('institution-list');
    if (!datalist) return;
    
    datalist.innerHTML = '';
    results.forEach(function(inst) {
        var option = document.createElement('option');
        option.value = inst.name;
        datalist.appendChild(option);
    });
}

// Table sorting - Client-side for current page
function sortTable(header) {
    var table = header.closest('table');
    var tbody = table.querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    var columnIndex = Array.from(header.parentNode.children).indexOf(header);
    var sortOrder = header.dataset.sortOrder || 'asc';
    
    rows.sort(function(a, b) {
        var aValue = a.cells[columnIndex].textContent.trim();
        var bValue = b.cells[columnIndex].textContent.trim();
        
        // Handle dates (DD/MM/YYYY or DD-MM-YYYY format)
        var dateRegex = /^\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}$/;
        if (dateRegex.test(aValue) && dateRegex.test(bValue)) {
            var aParts = aValue.split(/[\/-]/);
            var bParts = bValue.split(/[\/-]/);
            var aDate = new Date(aParts[2], aParts[1] - 1, aParts[0]);
            var bDate = new Date(bParts[2], bParts[1] - 1, bParts[0]);
            return sortOrder === 'asc' ? aDate - bDate : bDate - aDate;
        }
        
        // Try numeric comparison
        var aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
        var bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum) && aValue.match(/^[\d.,\s-]+$/)) {
            return sortOrder === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison (case-insensitive)
        return sortOrder === 'asc' 
            ? aValue.toLowerCase().localeCompare(bValue.toLowerCase()) 
            : bValue.toLowerCase().localeCompare(aValue.toLowerCase());
    });
    
    // Update sort order for next click
    header.dataset.sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    
    // Rebuild table body
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
    
    // Update sort indicator
    var headers = table.querySelectorAll('th.sortable');
    headers.forEach(function(h) {
        h.classList.remove('sort-asc', 'sort-desc');
    });
    header.classList.add(sortOrder === 'asc' ? 'sort-asc' : 'sort-desc');
}

// Server-side sorting - navigates with sort parameters while preserving all filters
function sortTableServer(sortBy, currentUrl) {
    var url = new URL(currentUrl || window.location.href);
    var currentSort = url.searchParams.get('sort') || '';
    var currentOrder = url.searchParams.get('order') || 'asc';
    
    // Toggle order if same column clicked
    var newOrder = (sortBy === currentSort && currentOrder === 'asc') ? 'desc' : 'asc';
    
    // Update sort parameters
    url.searchParams.set('sort', sortBy);
    url.searchParams.set('order', newOrder);
    url.searchParams.set('page', '1'); // Reset to first page on sort
    
    // All other parameters (filters) are automatically preserved since we're modifying the URL object
    window.location.href = url.toString();
}

// Initialize sortable tables
function initSortableTables() {
    var sortableHeaders = document.querySelectorAll('th.sortable[data-sort]');
    sortableHeaders.forEach(function(header) {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function(e) {
            e.preventDefault();
            var sortField = header.dataset.sort;
            if (header.dataset.serverSort === 'true') {
                sortTableServer(sortField);
            } else {
                sortTable(header);
            }
        });
    });
    
    // Mark current sort column from URL
    var urlParams = new URLSearchParams(window.location.search);
    var currentSort = urlParams.get('sort');
    var currentOrder = urlParams.get('order') || 'asc';
    
    if (currentSort) {
        var activeHeader = document.querySelector('th.sortable[data-sort="' + currentSort + '"]');
        if (activeHeader) {
            activeHeader.classList.add(currentOrder === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    }
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    var table = document.getElementById(tableId);
    if (!table) return;
    
    var rows = table.querySelectorAll('tr');
    var csv = [];
    
    rows.forEach(function(row) {
        var cols = row.querySelectorAll('th, td');
        var rowData = [];
        cols.forEach(function(col) {
            var text = col.textContent.trim().replace(/"/g, '""');
            rowData.push('"' + text + '"');
        });
        csv.push(rowData.join(','));
    });
    
    var csvContent = csv.join('\n');
    var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    var link = document.createElement('a');
    var url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename || 'export.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Toggle sidebar (for mobile)
function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return '-';
    var date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Show loading spinner
function showLoading(buttonId) {
    var button = document.getElementById(buttonId);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
    }
}

// Hide loading spinner
function hideLoading(buttonId, originalText) {
    var button = document.getElementById(buttonId);
    if (button) {
        button.disabled = false;
        button.innerHTML = originalText;
    }
}
