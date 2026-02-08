/**
 * AI Recruit - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initTooltips();
    initFormValidation();
    initFlashMessages();
    initFileUploads();
    initSearchFilters();
    initAnimations();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Auto-hide flash messages after 5 seconds
 */
function initFlashMessages() {
    var alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Initialize file upload previews
 */
function initFileUploads() {
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            var fileName = e.target.files[0] ? e.target.files[0].name : 'No file chosen';
            var label = input.nextElementSibling;
            if (label && label.classList.contains('form-label')) {
                // Update label if exists
            }
            
            // Show file size warning if too large
            if (e.target.files[0] && e.target.files[0].size > 10 * 1024 * 1024) {
                showAlert('warning', 'File size exceeds 10MB limit.');
                input.value = '';
            }
        });
    });
}

/**
 * Initialize search and filter functionality
 */
function initSearchFilters() {
    // Job search
    var searchForm = document.getElementById('jobSearchForm');
    if (searchForm) {
        var searchInput = searchForm.querySelector('input[name="search"]');
        var debounceTimer;
        
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(function() {
                    // Auto-submit after typing stops
                    // searchForm.submit();
                }, 500);
            });
        }
    }
}

/**
 * Initialize animations on scroll
 */
function initAnimations() {
    var animatedElements = document.querySelectorAll('[data-animate]');
    
    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-' + entry.target.dataset.animate);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        animatedElements.forEach(function(el) {
            observer.observe(el);
        });
    }
}

/**
 * Show alert message
 */
function showAlert(type, message) {
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.innerHTML = message + 
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    
    var container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(function() {
            alertDiv.remove();
        }, 5000);
    }
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
    var options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('success', 'Copied to clipboard!');
    }).catch(function(err) {
        console.error('Failed to copy:', err);
    });
}

/**
 * Confirm action dialog
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Loading state for buttons
 */
function setButtonLoading(button, loading) {
    if (loading) {
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
    }
}

/**
 * AJAX form submission
 */
function submitFormAjax(form, successCallback, errorCallback) {
    var formData = new FormData(form);
    var submitBtn = form.querySelector('button[type="submit"]');
    
    setButtonLoading(submitBtn, true);
    
    fetch(form.action, {
        method: form.method,
        body: formData
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        setButtonLoading(submitBtn, false);
        if (data.success) {
            if (successCallback) successCallback(data);
        } else {
            if (errorCallback) errorCallback(data);
        }
    })
    .catch(function(error) {
        setButtonLoading(submitBtn, false);
        console.error('Error:', error);
        showAlert('danger', 'An error occurred. Please try again.');
    });
}

/**
 * OTP Input Handler
 */
function initOtpInputs() {
    var otpInputs = document.querySelectorAll('.otp-input');
    
    otpInputs.forEach(function(input, index) {
        input.addEventListener('input', function(e) {
            var value = e.target.value;
            
            // Only allow numbers
            if (!/^\d*$/.test(value)) {
                e.target.value = '';
                return;
            }
            
            // Move to next input
            if (value.length === 1 && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
        });
        
        input.addEventListener('keydown', function(e) {
            // Move to previous input on backspace
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                otpInputs[index - 1].focus();
            }
        });
        
        // Handle paste
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            var pastedData = e.clipboardData.getData('text').replace(/\D/g, '');
            
            for (var i = 0; i < pastedData.length && i < otpInputs.length; i++) {
                otpInputs[i].value = pastedData[i];
            }
            
            if (pastedData.length >= otpInputs.length) {
                otpInputs[otpInputs.length - 1].focus();
            } else {
                otpInputs[pastedData.length].focus();
            }
        });
    });
}

/**
 * Chart initialization (requires Chart.js)
 */
function initCharts() {
    // Application Status Chart
    var statusChartEl = document.getElementById('statusChart');
    if (statusChartEl && typeof Chart !== 'undefined') {
        new Chart(statusChartEl, {
            type: 'doughnut',
            data: {
                labels: statusChartEl.dataset.labels ? JSON.parse(statusChartEl.dataset.labels) : [],
                datasets: [{
                    data: statusChartEl.dataset.values ? JSON.parse(statusChartEl.dataset.values) : [],
                    backgroundColor: ['#ffc107', '#0d6efd', '#198754', '#dc3545', '#6c757d']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Score Distribution Chart
    var scoreChartEl = document.getElementById('scoreChart');
    if (scoreChartEl && typeof Chart !== 'undefined') {
        new Chart(scoreChartEl, {
            type: 'bar',
            data: {
                labels: ['Resume', 'Confidence', 'Communication', 'Knowledge'],
                datasets: [{
                    label: 'Average Score',
                    data: scoreChartEl.dataset.values ? JSON.parse(scoreChartEl.dataset.values) : [0, 0, 0, 0],
                    backgroundColor: ['#0d6efd', '#6f42c1', '#20c997', '#fd7e14']
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

/**
 * Real-time form field validation
 */
function validateField(input) {
    var isValid = input.checkValidity();
    
    if (isValid) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    } else {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
    }
    
    return isValid;
}

/**
 * Email validation
 */
function isValidEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Password strength checker
 */
function checkPasswordStrength(password) {
    var strength = 0;
    
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    return strength; // 0-5 scale
}

/**
 * Dynamic role fields toggle (for registration)
 */
function toggleRoleFields() {
    var roleSelect = document.getElementById('role');
    var companyFields = document.getElementById('companyFields');
    var candidateFields = document.getElementById('candidateFields');
    
    if (roleSelect && companyFields && candidateFields) {
        roleSelect.addEventListener('change', function() {
            if (this.value === 'company') {
                companyFields.style.display = 'block';
                candidateFields.style.display = 'none';
            } else if (this.value === 'candidate') {
                companyFields.style.display = 'none';
                candidateFields.style.display = 'block';
            } else {
                companyFields.style.display = 'none';
                candidateFields.style.display = 'none';
            }
        });
    }
}

/**
 * Print interview results
 */
function printResults() {
    window.print();
}

/**
 * Export data to CSV
 */
function exportToCSV(data, filename) {
    var csv = '';
    
    // Headers
    if (data.length > 0) {
        csv += Object.keys(data[0]).join(',') + '\n';
    }
    
    // Rows
    data.forEach(function(row) {
        csv += Object.values(row).map(function(val) {
            return '"' + String(val).replace(/"/g, '""') + '"';
        }).join(',') + '\n';
    });
    
    // Download
    var blob = new Blob([csv], { type: 'text/csv' });
    var url = window.URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename + '.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Initialize additional components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    toggleRoleFields();
    initOtpInputs();
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initCharts();
    }
});
