// Main JavaScript for Smart Society Management System

// Voice alert function
function speakMessage(message) {
    if ('speechSynthesis' in window) {
        const speech = new SpeechSynthesisUtterance(message);
        speech.lang = 'en-US';
        speech.volume = 1;
        speech.rate = 1;
        speech.pitch = 1;
        window.speechSynthesis.speak(speech);
        
        // Show visual alert
        showVoiceAlert(message);
    }
}

// Offline emergency function
function triggerOfflineEmergency(emergencyType) {
    // Store emergency locally for later sync
    const emergencyData = {
        type: emergencyType,
        timestamp: new Date().toISOString(),
        flatNumber: 'A-101', // This would come from user session in real app
        status: 'pending'
    };
    
    // Store in localStorage
    let pendingEmergencies = JSON.parse(localStorage.getItem('pendingEmergencies') || '[]');
    pendingEmergencies.push(emergencyData);
    localStorage.setItem('pendingEmergencies', JSON.stringify(pendingEmergencies));
    
    // Show offline notification
    showNotification(`${emergencyType} emergency recorded. Will be sent when connection is restored.`, 'warning');
    
    // Trigger appropriate offline action based on emergency type
    switch(emergencyType) {
        case 'Medical':
            // In a real app, this would trigger native phone dialer
            showNotification('Dialing 108 for medical emergency...', 'info');
            break;
        case 'Police':
            // In a real app, this would trigger native phone dialer
            showNotification('Dialing 112 for police emergency...', 'info');
            break;
        case 'Fire':
            // In a real app, this would trigger native phone dialer
            showNotification('Dialing 101 for fire emergency...', 'info');
            break;
        case 'SMS':
            // In a real app, this would trigger SMS sending
            showNotification('Preparing emergency SMS...', 'info');
            break;
        case 'WhatsApp':
            // In a real app, this would trigger WhatsApp sharing
            showNotification('Preparing WhatsApp message...', 'info');
            break;
    }
}

// Sync pending emergencies when online
function syncPendingEmergencies() {
    if (navigator.onLine) {
        const pendingEmergencies = JSON.parse(localStorage.getItem('pendingEmergencies') || '[]');
        
        if (pendingEmergencies.length > 0) {
            // In a real app, this would send data to server
            console.log('Syncing pending emergencies:', pendingEmergencies);
            
            // Clear synced emergencies
            localStorage.removeItem('pendingEmergencies');
            
            showNotification(`${pendingEmergencies.length} emergency records synced successfully!`, 'success');
        }
    }
}

// Check connection status
function checkConnectionStatus() {
    const isOnline = navigator.onLine;
    const statusElement = document.getElementById('connectionStatus');
    
    if (statusElement) {
        if (isOnline) {
            statusElement.className = 'badge bg-success';
            statusElement.textContent = 'Online';
        } else {
            statusElement.className = 'badge bg-danger';
            statusElement.textContent = 'Offline';
        }
    }
    
    return isOnline;
}

// Show visual voice alert
function showVoiceAlert(message) {
    const alertBox = document.createElement('div');
    alertBox.className = 'voice-alert';
    alertBox.innerHTML = `
        <i class="fas fa-volume-up me-2"></i>
        ${message}
        <button type="button" class="btn-close btn-close-white ms-2" onclick="this.parentElement.style.display='none'"></button>
    `;
    
    document.body.appendChild(alertBox);
    alertBox.style.display = 'block';
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        alertBox.style.display = 'none';
        alertBox.remove();
    }, 5000);
}

// Form validation
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        // Reset validation state
        input.classList.remove('is-invalid');
        if (input.nextElementSibling && input.nextElementSibling.classList.contains('invalid-feedback')) {
            input.nextElementSibling.remove();
        }
        
        // Check if field is empty
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('is-invalid');
            
            // Create error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = 'This field is required';
            input.parentNode.insertBefore(errorDiv, input.nextSibling);
            return;
        }
        
        // Specific validation for email
        if (input.type === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value)) {
                isValid = false;
                input.classList.add('is-invalid');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = 'Please enter a valid email address';
                input.parentNode.insertBefore(errorDiv, input.nextSibling);
                return;
            }
        }
        
        // Specific validation for phone numbers
        if (input.type === 'tel') {
            const phoneRegex = /^[0-9]{10}$/;
            if (!phoneRegex.test(input.value.replace(/\D/g, ''))) {
                isValid = false;
                input.classList.add('is-invalid');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = 'Please enter a valid 10-digit phone number';
                input.parentNode.insertBefore(errorDiv, input.nextSibling);
                return;
            }
        }
        
        // Specific validation for vehicle numbers
        if (input.id === 'vehicleNumber') {
            const vehicleRegex = /^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$/;
            if (!vehicleRegex.test(input.value.toUpperCase())) {
                isValid = false;
                input.classList.add('is-invalid');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = 'Please enter a valid vehicle number (e.g., MH12AB1234)';
                input.parentNode.insertBefore(errorDiv, input.nextSibling);
                return;
            }
        }
    });
    
    return isValid;
}

// Enhanced form validation with real-time feedback
function setupRealTimeValidation(form) {
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        // Validate on blur
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        // Clear error on focus
        input.addEventListener('focus', function() {
            this.classList.remove('is-invalid');
            if (this.nextElementSibling && this.nextElementSibling.classList.contains('invalid-feedback')) {
                this.nextElementSibling.remove();
            }
        });
        
        // Validate on input for immediate feedback
        input.addEventListener('input', function() {
            // Only validate if field was previously invalid
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

// Validate individual field
function validateField(field) {
    // Clear previous validation
    field.classList.remove('is-invalid');
    if (field.nextElementSibling && field.nextElementSibling.classList.contains('invalid-feedback')) {
        field.nextElementSibling.remove();
    }
    
    // Check if field is required and empty
    if (field.hasAttribute('required') && !field.value.trim()) {
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        
        // Provide specific error message based on field type
        if (field.id === 'name') {
            errorDiv.textContent = 'Please enter your full name';
        } else if (field.id === 'email') {
            errorDiv.textContent = 'Please enter your email address';
        } else if (field.id === 'mobile') {
            errorDiv.textContent = 'Please enter your mobile number';
        } else if (field.id === 'block') {
            errorDiv.textContent = 'Please select a block';
        } else if (field.id === 'flat_number') {
            errorDiv.textContent = 'Please select a flat number';
        } else if (field.id === 'user_type') {
            errorDiv.textContent = 'Please select user type';
        } else if (field.id === 'password') {
            errorDiv.textContent = 'Please enter a password';
        } else if (field.id === 'confirm_password') {
            errorDiv.textContent = 'Please confirm your password';
        } else {
            errorDiv.textContent = 'This field is required';
        }
        
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
        return false;
    }
    
    // Specific validations
    if (field.type === 'email' && field.value.trim()) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(field.value)) {
            field.classList.add('is-invalid');
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = 'Please enter a valid email address';
            field.parentNode.insertBefore(errorDiv, field.nextSibling);
            return false;
        }
    }
    
    if (field.type === 'tel' && field.value.trim()) {
        const phoneRegex = /^[0-9]{10}$/;
        if (!phoneRegex.test(field.value.replace(/\D/g, ''))) {
            field.classList.add('is-invalid');
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = 'Please enter a valid 10-digit phone number';
            field.parentNode.insertBefore(errorDiv, field.nextSibling);
            return false;
        }
    }
    
    if (field.id === 'vehicleNumber' && field.value.trim()) {
        const vehicleRegex = /^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$/;
        if (!vehicleRegex.test(field.value.toUpperCase())) {
            field.classList.add('is-invalid');
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = 'Please enter a valid vehicle number (e.g., MH12AB1234)';
            field.parentNode.insertBefore(errorDiv, field.nextSibling);
            return false;
        }
    }
    
    // Specific validation for password confirmation
    if (field.id === 'confirm_password' && field.value.trim()) {
        const passwordField = document.getElementById('password');
        if (passwordField && field.value !== passwordField.value) {
            field.classList.add('is-invalid');
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = 'Passwords do not match';
            field.parentNode.insertBefore(errorDiv, field.nextSibling);
            return false;
        }
    }
    
    return true;
}

// Handle form submissions with validation
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Set up real-time validation
        setupRealTimeValidation(form);
        
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                speakMessage('Please correct the errors in the form');
            }
        });
    });
    
    // Add event listeners for buttons that need voice feedback
    const voiceButtons = document.querySelectorAll('[data-voice]');
    voiceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const message = this.getAttribute('data-voice');
            if (message) {
                speakMessage(message);
            }
        });
    });
});

// AJAX helper function
async function ajaxRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('AJAX Request failed:', error);
        return { success: false, message: 'Request failed' };
    }
}

// Utility function to format dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Utility function to show notification
function showNotification(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    
    // Remove toast from DOM after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
    return container;
}

// Confirm dialog for critical actions
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}