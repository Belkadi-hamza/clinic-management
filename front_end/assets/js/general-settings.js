// front_end/assets/js/general-settings.js

// Load user information on page load
window.addEventListener('DOMContentLoaded', function () {
    loadUserProfile();
    setupFormSubmission();
});

// Load user profile data
async function loadUserProfile() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showError('Veuillez vous connecter pour accéder à votre profil.');
        window.location.href = 'login.html';
        return;
    }

    try {
        setFormLoading(true);

        // Load departments first
        await loadDepartments();

        const response = await fetch(apiUrl('/auth/me'), {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });

        if (response.ok) {
            const user = await response.json();
            populateFormWithUserData(user);
        } else if (response.status === 401) {
            localStorage.removeItem('access_token');
            showError('Votre session a expiré. Veuillez vous reconnecter.');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            throw new Error('Échec de la récupération du profil utilisateur');
        }
    } catch (error) {
        console.error('Erreur lors du chargement du profil utilisateur:', error);
        if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
            showError('Impossible de se connecter au serveur. Veuillez vérifier votre connexion et réessayer.', true);
        } else {
            showError('Impossible de charger les informations du profil. Veuillez réessayer.');
        }
    } finally {
        setFormLoading(false);
    }
}

// Load departments from API
async function loadDepartments() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(apiUrl('/api/departments/'), {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        });

        if (response.ok) {
            const departments = await response.json();
            populateDepartmentSelect(departments);
        } else {
            console.error('Failed to load departments');
        }
    } catch (error) {
        console.error('Error loading departments:', error);
    }
}

// Populate department select dropdown
function populateDepartmentSelect(departments) {
    const departmentSelect = document.getElementById('department');
    if (departmentSelect) {
        // Clear existing options except the first one
        departmentSelect.innerHTML = '<option value="">Sélectionner un département</option>';
        
        departments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept.id;
            option.textContent = dept.name;
            departmentSelect.appendChild(option);
        });
    }
}

// Check if user is a doctor based on role and staff.is_doctor field
function isDoctor(user) {    
    // Check if staff.is_doctor is true (if field exists)
    const isStaffDoctor = user.is_doctor === true || user.is_doctor === 'true';
    
    return isStaffDoctor;
}
// Show/hide doctor-specific fields with smooth animation
function toggleDoctorFields(show) {
    const doctorFields = document.querySelectorAll('.doctor-field');
    doctorFields.forEach(field => {
        if (show) {
            field.classList.remove('hide');
            field.classList.add('show');
            field.style.display = 'block';
        } else {
            field.classList.remove('show');
            field.classList.add('hide');
            // Hide after animation completes
            setTimeout(() => {
                if (field.classList.contains('hide')) {
                    field.style.display = 'none';
                }
            }, 300);
        }
    });
}

// Populate form with user data
function populateFormWithUserData(user) {
    // Store current user globally
    currentUser = user;
    
    // Personal Information
    setValue('first_name', user.first_name || '');
    setValue('last_name', user.last_name || '');

    // Format date for input[type="date"]
    if (user.date_of_birth) {
        const date = new Date(user.date_of_birth);
        const formattedDate = date.toISOString().split('T')[0];
        setValue('date_of_birth', formattedDate);
    }

    // Gender select
    setSelectValue('gender', user.gender || '');

    // Marital Status - set select value
    setSelectValue('marital_status', user.marital_status || '');

    // Contact Information
    setValue('mobile_phone', user.mobile_phone || '');
    setValue('home_phone', user.home_phone || '');
    setValue('fax', user.fax || '');
    setValue('email', user.email || '');

    // Address Information
    setValue('line', user.line || '');
    setSelectValue('city', user.city || '');

    // Professional Information
    setSelectValue('department_id', user.department_id || '');
    setValue('specialization', user.specialization || '');
    
    // Doctor-specific fields - populate and set checkbox state
    const isUserDoctor = isDoctor(user);
    setValue('is_doctor', isUserDoctor);
    
    if (isUserDoctor) {
        setValue('doctor_code', user.doctor_code || '');
        setValue('license_number', user.license_number || '');
        toggleDoctorFields(true);
    } else {
        setValue('doctor_code', '');
        setValue('license_number', '');
        toggleDoctorFields(false);
    }
    
    // Setup checkbox event listener
    setupDoctorCheckboxListener();
}

// Helper function to set form values
function setValue(fieldName, value) {
    const element = document.querySelector(`[name="${fieldName}"]`);
    if (element) {
        if (element.type === 'checkbox') {
            element.checked = Boolean(value);
        } else {
            element.value = value;
        }
    }
}

// Helper function to set select dropdown values
function setSelectValue(fieldName, value) {
    const selectElement = document.querySelector(`select[name="${fieldName}"]`);
    if (selectElement && value) {
        // Set the value
        selectElement.value = value;
        
        // If using Select2, trigger change event
        if ($(selectElement).hasClass('select') || $(selectElement).hasClass('select2')) {
            $(selectElement).val(value).trigger('change');
        }
    }
}

// Setup doctor checkbox listener
function setupDoctorCheckboxListener() {
    const checkbox = document.getElementById('is_doctor_checkbox');
    if (checkbox) {
        checkbox.addEventListener('change', function() {
            const isChecked = this.checked;
            toggleDoctorFields(isChecked);
            
            // Clear doctor fields when unchecked
            if (!isChecked) {
                setValue('doctor_code', '');
                setValue('license_number', '');
            }
        });
    }
}

// Setup form submission
function setupFormSubmission() {
    const form = document.getElementById('general-settings-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // Add input validation
    setupFormValidation();
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        showError('Veuillez vous connecter pour mettre à jour votre profil.');
        return;
    }

    if (!validateForm()) {
        return;
    }

    try {
        setFormLoading(true, 'Saving...');
        
        const formData = getFormData();
        
        console.log('Form data to send:', formData);

        const response = await fetch(apiUrl('/api/staff/me/update'), {
            method: 'PUT',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const data = await response.json();
            showSuccess('Profile updated successfully!');
            updateLocalStorage(data);
        } else if (response.status === 401) {
            localStorage.removeItem('access_token');
            showError('Votre session a expiré. Veuillez vous reconnecter.');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Échec de la mise à jour du profil (${response.status})`);
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        let errorMessage = 'Échec de la mise à jour du profil. ';
        
        if (error.message.includes('Email already exists')) {
            errorMessage += 'L\'adresse e-mail est déjà utilisée.';
        } else if (error.message === 'Échec de la récupération' || error.name === 'TypeError') {
            errorMessage += 'Impossible de se connecter au serveur. Veuillez vérifier votre connexion.';
        } else {
            errorMessage += error.message || 'Veuillez réessayer.';
        }
        
        showError(errorMessage);
    } finally {
        setFormLoading(false, 'Sauvegarder les modifications');
    }
}


// Get form data as object
function getFormData() {
    const form = document.getElementById('general-settings-form');
    const formData = new FormData(form);
    const data = {};

    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        // Skip empty values for optional fields
        if (value === '' && !isRequiredField(key)) {
            continue;
        }
        
        // Handle checkbox for is_doctor
        if (key === 'is_doctor') {
            data[key] = true; // Checkbox is checked
            continue;
        }
        
        // Skip doctor fields if checkbox is not checked
        if (isDoctorField(key) && !document.getElementById('is_doctor_checkbox').checked) {
            continue;
        }
        
        // Convert department_id to integer if it exists
        if (key === 'department_id' && value) {
            data[key] = parseInt(value);
        } else {
            data[key] = value;
        }
    }

    // Add is_doctor field based on checkbox state
    data.is_doctor = document.getElementById('is_doctor_checkbox').checked;

    return data;
}

// Check if field is doctor-specific
function isDoctorField(fieldName) {
    const doctorFields = ['doctor_code', 'license_number'];
    return doctorFields.includes(fieldName);
}

// Store current user globally for access in other functions
let currentUser = null;

// Check if field is required
function isRequiredField(fieldName) {
    const requiredFields = ['first_name', 'last_name'];
    return requiredFields.includes(fieldName);
}

// Validate form data
function validateForm() {
    const form = document.getElementById('general-settings-form');
    let isValid = true;

    // Clear previous validation
    clearValidation();

    // Required fields validation
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        // Skip doctor fields if checkbox is not checked
        if (isDoctorField(field.name) && !document.getElementById('is_doctor_checkbox').checked) {
            return;
        }
        
        if (!field.value.trim()) {
            markFieldInvalid(field, 'Ce champ est obligatoire');
            isValid = false;
        }
    });

    // Email validation
    const emailField = form.querySelector('[name="email"]');
    if (emailField.value && !isValidEmail(emailField.value)) {
        markFieldInvalid(emailField, 'Veuillez entrer une adresse e-mail valide');
        isValid = false;
    }

    // Phone validation (basic)
    const phoneFields = form.querySelectorAll('[name="mobile_phone"], [name="home_phone"]');
    phoneFields.forEach(field => {
        if (field.value && !isValidPhone(field.value)) {
            markFieldInvalid(field, 'Veuillez entrer un numéro de téléphone valide');
            isValid = false;
        }
    });

    return isValid;
}

// Setup form validation
function setupFormValidation() {
    const form = document.getElementById('general-settings-form');

    // Real-time validation
    form.addEventListener('input', function (e) {
        const field = e.target;
        clearFieldValidation(field);

        // Skip doctor fields if checkbox is not checked
        if (isDoctorField(field.name) && !document.getElementById('is_doctor_checkbox').checked) {
            return;
        }

        if (field.hasAttribute('required') && !field.value.trim()) {
            markFieldInvalid(field, 'Ce champ est obligatoire');
        } else if (field.name === 'email' && field.value && !isValidEmail(field.value)) {
            markFieldInvalid(field, 'Veuillez entrer une adresse e-mail valide');
        }
    });
}

// Validation helpers
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    // Basic phone validation - adjust as needed
    const phoneRegex = /^[\d\s\(\)\-\.\+]+$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
}

// UI helpers for validation
function markFieldInvalid(field, message) {
    field.classList.add('is-invalid');

    let feedback = field.nextElementSibling;
    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        field.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
}

function clearFieldValidation(field) {
    field.classList.remove('is-invalid');
    const feedback = field.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.remove();
    }
}

function clearValidation() {
    const form = document.getElementById('general-settings-form');
    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });

    const feedbacks = form.querySelectorAll('.invalid-feedback');
    feedbacks.forEach(feedback => feedback.remove());
}

// Update localStorage with new user data
function updateLocalStorage(userData) {
    // Update user name in localStorage if available
    if (userData.first_name && userData.last_name) {
        localStorage.setItem('user_name', `${userData.first_name} ${userData.last_name}`);
    }

    // Update other user info as needed
    if (userData.department_id) {
        localStorage.setItem('user_department_id', userData.department_id);
    }
    if (userData.specialization) {
        localStorage.setItem('user_specialization', userData.specialization);
    }
    if (userData.doctor_code) {
        localStorage.setItem('user_doctor_code', userData.doctor_code);
    }
    if (userData.is_doctor !== undefined) {
        localStorage.setItem('user_is_doctor', userData.is_doctor);
    }
}

// Form loading state
function setFormLoading(loading, buttonText = 'Enregistrer les modifications') {
    const submitBtn = document.querySelector('#general-settings-form button[type="submit"]');
    const cancelBtn = document.querySelector('#general-settings-form button[type="reset"]');

    if (loading) {
        submitBtn.disabled = true;
        cancelBtn.disabled = true;
        submitBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${buttonText}
        `;
    } else {
        submitBtn.disabled = false;
        cancelBtn.disabled = false;
        submitBtn.textContent = buttonText;
    }
}

// Alert functions
function showError(message, showRetry = false) {
    hideMessages();

    // Create error alert if it doesn't exist
    let errorAlert = document.getElementById('errorAlert');
    if (!errorAlert) {
        errorAlert = document.createElement('div');
        errorAlert.id = 'errorAlert';
        errorAlert.className = 'alert alert-danger alert-dismissible fade show';
        errorAlert.innerHTML = `
            <span id="errorMessage"></span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const form = document.getElementById('general-settings-form');
        form.parentNode.insertBefore(errorAlert, form);
    }

    document.getElementById('errorMessage').textContent = message;
    errorAlert.style.display = 'block';

    // Auto-hide after 8 seconds for non-critical errors
    if (!showRetry) {
        setTimeout(() => {
            errorAlert.style.display = 'none';
        }, 8000);
    }
}

function showSuccess(message) {
    hideMessages();

    // Create success alert if it doesn't exist
    let successAlert = document.getElementById('successAlert');
    if (!successAlert) {
        successAlert = document.createElement('div');
        successAlert.id = 'successAlert';
        successAlert.className = 'alert alert-success alert-dismissible fade show';
        successAlert.innerHTML = `
            <span id="successMessage"></span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const form = document.getElementById('general-settings-form');
        form.parentNode.insertBefore(successAlert, form);
    }

    document.getElementById('successMessage').textContent = message;
    successAlert.style.display = 'block';

    // Auto-hide after 4 seconds
    setTimeout(() => {
        successAlert.style.display = 'none';
    }, 4000);
}

function hideMessages() {
    const errorAlert = document.getElementById('errorAlert');
    const successAlert = document.getElementById('successAlert');

    if (errorAlert) errorAlert.style.display = 'none';
    if (successAlert) successAlert.style.display = 'none';
}

// Handle cancel button
document.addEventListener('DOMContentLoaded', function () {
    const cancelBtn = document.querySelector('#general-settings-form button[type="reset"]');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function () {
            // Reload the form with original data
            loadUserProfile();
            hideMessages();
        });
    }
});