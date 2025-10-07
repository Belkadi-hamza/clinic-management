// Security Settings JavaScript
document.addEventListener('DOMContentLoaded', function() {
    setupPasswordChangeForm();
    setupPasswordToggle();
});

// Setup password change form submission
function setupPasswordChangeForm() {
    const form = document.querySelector('#change_password form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Get form inputs
        const currentPassword = form.querySelector('input[name="current_password"]');
        const newPassword = form.querySelector('input[name="new_password"]');
        const confirmPassword = form.querySelector('input[name="confirm_password"]');

        // Validate inputs
        if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
            showAlert('error', 'All password fields are required');
            return;
        }

        // Check if new passwords match
        if (newPassword.value !== confirmPassword.value) {
            showAlert('error', 'New password and confirm password do not match');
            return;
        }

        // Check password strength (minimum 8 characters)
        if (newPassword.value.length < 8) {
            showAlert('error', 'Password must be at least 8 characters long');
            return;
        }

        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                window.location.href = 'login.html';
                return;
            }

            const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    current_password: currentPassword.value,
                    new_password: newPassword.value
                })
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('success', 'Password changed successfully');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('change_password'));
                if (modal) {
                    modal.hide();
                }

                // Reset form
                form.reset();

                // Optional: Logout user and redirect to login
                setTimeout(() => {
                    localStorage.removeItem('access_token');
                    window.location.href = 'login.html';
                }, 2000);
            } else {
                showAlert('error', data.detail || 'Failed to change password');
            }
        } catch (error) {
            console.error('Error changing password:', error);
            showAlert('error', 'An error occurred while changing password');
        }
    });
}

// Setup password visibility toggle
function setupPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-password');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('ti-eye-off');
                icon.classList.add('ti-eye');
            } else {
                input.type = 'password';
                icon.classList.remove('ti-eye');
                icon.classList.add('ti-eye-off');
            }
        });
    });
}

// Show alert message
function showAlert(type, message) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-custom');
    existingAlerts.forEach(alert => alert.remove());

    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show alert-custom`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        <strong>${type === 'success' ? 'Success!' : 'Error!'}</strong> ${message}
    `;

    document.body.appendChild(alertDiv);

    // Auto remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
