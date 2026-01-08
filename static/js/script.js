/**
 * JPHN Transfer Management System - Web Application
 * Main JavaScript file
 */

// ===== THEME TOGGLE =====
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    
    // Load saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
    
    function updateThemeIcon(theme) {
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
            }
        }
    }
});

// ===== AUTO-DISMISS FLASH MESSAGES =====
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(msg) {
        setTimeout(function() {
            msg.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(function() {
                msg.remove();
            }, 300);
        }, 5000);
    });
});

// Add slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===== DATE INPUT FORMATTING =====
function formatDateInput(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length >= 2) {
        value = value.slice(0, 2) + '-' + value.slice(2);
    }
    if (value.length >= 5) {
        value = value.slice(0, 5) + '-' + value.slice(5, 9);
    }
    input.value = value;
}

document.querySelectorAll('.date-input').forEach(function(input) {
    input.addEventListener('input', function(e) {
        formatDateInput(e.target);
    });
});

// ===== TABLE SORTING =====
function sortTable(table, column, asc = true) {
    const dirModifier = asc ? 1 : -1;
    const tBody = table.tBodies[0];
    const rows = Array.from(tBody.querySelectorAll('tr'));
    
    const sortedRows = rows.sort((a, b) => {
        const aColText = a.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
        const bColText = b.querySelector(`td:nth-child(${column + 1})`).textContent.trim();
        
        return aColText > bColText ? (1 * dirModifier) : (-1 * dirModifier);
    });
    
    while (tBody.firstChild) {
        tBody.removeChild(tBody.firstChild);
    }
    
    tBody.append(...sortedRows);
}

// ===== TABLE SEARCH/FILTER =====
function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    input.addEventListener('input', function() {
        const filter = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(function(row) {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });
}

// ===== CONFIRM DELETE =====
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// ===== FORM VALIDATION =====
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('error');
            
            // Show error message
            let errorMsg = field.parentElement.querySelector('.error-message');
            if (!errorMsg) {
                errorMsg = document.createElement('span');
                errorMsg.className = 'error-message';
                errorMsg.style.color = 'var(--danger-color)';
                errorMsg.style.fontSize = '0.8rem';
                field.parentElement.appendChild(errorMsg);
            }
            errorMsg.textContent = 'This field is required';
        } else {
            field.classList.remove('error');
            const errorMsg = field.parentElement.querySelector('.error-message');
            if (errorMsg) {
                errorMsg.remove();
            }
        }
    });
    
    return isValid;
}

// ===== SELECT ALL CHECKBOXES =====
function setupSelectAll(selectAllId, checkboxClass) {
    const selectAll = document.getElementById(selectAllId);
    if (!selectAll) return;
    
    selectAll.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.' + checkboxClass);
        checkboxes.forEach(function(cb) {
            cb.checked = selectAll.checked;
        });
        updateSelectedCount(checkboxClass);
    });
    
    // Individual checkbox change
    document.querySelectorAll('.' + checkboxClass).forEach(function(cb) {
        cb.addEventListener('change', function() {
            updateSelectedCount(checkboxClass);
        });
    });
}

function updateSelectedCount(checkboxClass) {
    const checkboxes = document.querySelectorAll('.' + checkboxClass);
    const checked = document.querySelectorAll('.' + checkboxClass + ':checked').length;
    const countElement = document.querySelector('.selected-count');
    if (countElement) {
        countElement.textContent = checked + ' selected';
    }
}

// ===== PREFERENCE DROPDOWN VALIDATION =====
function setupPreferenceDropdowns() {
    const prefSelects = document.querySelectorAll('.pref-select');
    
    prefSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            updatePreferenceOptions();
        });
    });
    
    function updatePreferenceOptions() {
        const selectedValues = [];
        prefSelects.forEach(function(s) {
            if (s.value) {
                selectedValues.push(s.value);
            }
        });
        
        prefSelects.forEach(function(select) {
            const currentValue = select.value;
            Array.from(select.options).forEach(function(option) {
                if (option.value && option.value !== currentValue && selectedValues.includes(option.value)) {
                    option.disabled = true;
                    option.style.color = 'var(--text-muted)';
                } else {
                    option.disabled = false;
                    option.style.color = '';
                }
            });
        });
    }
}

// Initialize preference dropdowns if they exist
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.pref-select')) {
        setupPreferenceDropdowns();
    }
});

// ===== NUMBER INPUT VALIDATION =====
function setupNumberInputs() {
    const numberInputs = document.querySelectorAll('input[type="number"]');
    
    numberInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            if (parseInt(this.value) < 0) {
                this.value = 0;
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', setupNumberInputs);

// ===== LOADING STATE =====
function setLoading(element, loading = true) {
    if (loading) {
        element.disabled = true;
        element.dataset.originalText = element.innerHTML;
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    } else {
        element.disabled = false;
        element.innerHTML = element.dataset.originalText;
    }
}

// ===== AJAX HELPER =====
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// ===== PRINT FUNCTIONALITY =====
function printTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const printWindow = window.open('', '', 'width=800,height=600');
    printWindow.document.write('<html><head><title>Print</title>');
    printWindow.document.write('<style>');
    printWindow.document.write(`
        body { font-family: Arial, sans-serif; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        @media print { body { -webkit-print-color-adjust: exact; } }
    `);
    printWindow.document.write('</style></head><body>');
    printWindow.document.write('<h2>JPHN Transfer Management System</h2>');
    printWindow.document.write(table.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

// ===== EXPORT TO CSV (client-side) =====
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('th, td');
        const rowData = [];
        cols.forEach(function(col) {
            // Skip action columns
            if (!col.classList.contains('action-cell')) {
                let text = col.textContent.replace(/"/g, '""');
                rowData.push('"' + text + '"');
            }
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (navigator.msSaveBlob) {
        navigator.msSaveBlob(blob, filename);
    } else {
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    }
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save (prevent default)
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        const saveBtn = document.querySelector('button[type="submit"]');
        if (saveBtn) {
            e.preventDefault();
            saveBtn.click();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(function(modal) {
            if (modal.style.display === 'flex') {
                modal.style.display = 'none';
            }
        });
    }
});

// ===== TOOLTIPS =====
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[title]');
    
    tooltipElements.forEach(function(el) {
        el.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.getAttribute('title');
            tooltip.style.cssText = `
                position: absolute;
                background: var(--text-primary);
                color: var(--bg-primary);
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
                z-index: 9999;
                pointer-events: none;
            `;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.bottom + 5) + 'px';
            
            this._tooltip = tooltip;
        });
        
        el.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

// ===== UTILITY FUNCTIONS =====
function debounce(func, wait) {
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

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDuration(days) {
    if (!days || days <= 0) return '0D';
    
    const years = Math.floor(days / 365);
    const remaining = days % 365;
    const months = Math.floor(remaining / 30);
    const daysLeft = remaining % 30;
    
    const parts = [];
    if (years > 0) parts.push(years + 'Y');
    if (months > 0) parts.push(months + 'M');
    if (daysLeft > 0 || parts.length === 0) parts.push(daysLeft + 'D');
    
    return parts.join(' ');
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    // Initialize select all if exists
    if (document.getElementById('selectAll')) {
        setupSelectAll('selectAll', 'emp-checkbox');
    }
    
    // Initialize tooltips
    // initTooltips(); // Uncomment if needed
    
    console.log('JPHN Transfer Web App initialized');
});
