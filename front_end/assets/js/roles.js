// Roles Settings JavaScript
let roles = [];
let currentEditRoleId = null;
let currentDeleteRoleId = null;
let isLoading = false;

document.addEventListener('DOMContentLoaded', function() {
    loadRoles();
    setupAddRoleForm();
    setupEditRoleForm();
    setupDeleteConfirmation();
    setupFormValidation();
});

// Load all roles from API
async function loadRoles() {
    if (isLoading) return;
    
    try {
        isLoading = true;
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        setLoadingState(true);

        const response = await fetch(`${API_BASE_URL}/api/roles`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Loaded roles:', data);
            // Filter out superadmin role
            roles = data.filter(role => role.name.toLowerCase() !== 'superadmin');
            renderRolesTable();
            updateRoleCount();
        } else if (response.status === 401) {
            localStorage.removeItem('access_token');
            showAlert('error', 'Votre session a expiré. Veuillez vous reconnecter.');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            console.error('Failed to load roles. Status:', response.status);
            const errorData = await response.json().catch(() => ({}));
            console.error('Error details:', errorData);
            showAlert('error', errorData.detail || 'Échec du chargement des rôles');
            renderRolesTable(); // Show empty state
        }
    } catch (error) {
        console.error('Error loading roles:', error);
        showAlert('error', 'Une erreur s\'est produite lors du chargement des rôles: ' + error.message);
        renderRolesTable(); // Show empty state
    } finally {
        isLoading = false;
        setLoadingState(false);
    }
}

// Render roles table
function renderRolesTable() {
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    if (roles.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <div class="text-muted">
                        <i class="ti ti-users-off fs-48 mb-3 d-block"></i>
                        <p class="mb-0">Aucun rôle trouvé</p>
                        <small>Cliquez sur "Nouveau rôle" pour commencer</small>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = roles.map(role => `
        <tr>
            <td>${escapeHtml(role.name)}</td>
            <td>${escapeHtml(role.description || 'N/A')}</td>
            <td>${getStatusBadge(role.status)}</td>
            <td>${formatDate(role.created_at)}</td>
            <td class="text-end">
                <a href="javascript:void(0);" class="btn btn-icon btn-outline-light" data-bs-toggle="dropdown" aria-label="more options">
                    <i class="ti ti-dots-vertical"></i>
                </a>
                <ul class="dropdown-menu p-2">
                    <li>
                        <a href="javascript:void(0);" class="dropdown-item d-flex align-items-center" onclick="openEditModal(${role.id})">
                            <i class="ti ti-edit me-1"></i>Modifier
                        </a>
                    </li>
                    <li>
                        <a href="javascript:void(0);" class="dropdown-item d-flex align-items-center text-danger" onclick="openDeleteModal(${role.id})">
                            <i class="ti ti-trash me-1"></i>Supprimer
                        </a>
                    </li>
                </ul>
            </td>
        </tr>
    `).join('');
}

// Update role count badge
function updateRoleCount() {
    const countBadge = document.getElementById('role-count');
    if (countBadge) {
        countBadge.textContent = roles.length;
    }
}

// Setup add role form
function setupAddRoleForm() {
    const form = document.getElementById('add-role-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = {
            name: document.getElementById('add-role-name').value.trim(),
            description: document.getElementById('add-role-description').value.trim()
        };

        if (!formData.name.trim()) {
            showAlert('error', 'Le nom du rôle est obligatoire');
            return;
        }

        // Check if role name already exists
        const existingRole = roles.find(role => 
            role.name.toLowerCase() === formData.name.toLowerCase()
        );
        if (existingRole) {
            showAlert('error', 'Un rôle avec ce nom existe déjà');
            return;
        }

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${API_BASE_URL}/api/roles`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('success', 'Rôle créé avec succès');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('add_role'));
                if (modal) modal.hide();
                
                // Reset form
                form.reset();
                clearFormValidation(form);
                
                // Reload roles
                await loadRoles();
            } else {
                showAlert('error', data.detail || 'Échec de la création du rôle');
            }
        } catch (error) {
            console.error('Error creating role:', error);
            showAlert('error', 'Une erreur s\'est produite lors de la création du rôle');
        }
    });
}

// Setup edit role form
function setupEditRoleForm() {
    const form = document.getElementById('edit-role-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const roleId = document.getElementById('edit-role-id').value;
        const formData = {
            name: document.getElementById('edit-role-name').value.trim(),
            description: document.getElementById('edit-role-description').value.trim()
        };

        if (!formData.name.trim()) {
            showAlert('error', 'Le nom du rôle est obligatoire');
            return;
        }

        // Check if role name already exists (excluding current role)
        const existingRole = roles.find(role => 
            role.name.toLowerCase() === formData.name.toLowerCase() && 
            role.id !== parseInt(roleId)
        );
        if (existingRole) {
            showAlert('error', 'Un rôle avec ce nom existe déjà');
            return;
        }

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${API_BASE_URL}/api/roles/${roleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('success', 'Rôle mis à jour avec succès');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('edit_role'));
                if (modal) modal.hide();
                
                // Reload roles
                await loadRoles();
            } else {
                showAlert('error', data.detail || 'Échec de la mise à jour du rôle');
            }
        } catch (error) {
            console.error('Error updating role:', error);
            showAlert('error', 'Une erreur s\'est produite lors de la mise à jour du rôle');
        }
    });
}

// Setup delete confirmation
function setupDeleteConfirmation() {
    const deleteBtn = document.getElementById('confirm-delete-role');
    if (!deleteBtn) return;

    deleteBtn.addEventListener('click', async function() {
        const roleId = document.getElementById('delete-role-id').value;
        if (!roleId) return;

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${API_BASE_URL}/api/roles/${roleId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                showAlert('success', 'Rôle supprimé avec succès');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('delete_modal'));
                if (modal) modal.hide();
                
                // Reload roles
                await loadRoles();
            } else {
                const data = await response.json();
                showAlert('error', data.detail || 'Échec de la suppression du rôle');
            }
        } catch (error) {
            console.error('Error deleting role:', error);
            showAlert('error', 'Une erreur s\'est produite lors de la suppression du rôle');
        }
    });
}

// Open edit modal with role data
function openEditModal(roleId) {
    const role = roles.find(r => r.id === roleId);
    if (!role) return;

    document.getElementById('edit-role-id').value = role.id;
    document.getElementById('edit-role-name').value = role.name;
    document.getElementById('edit-role-description').value = role.description || '';

    const modal = new bootstrap.Modal(document.getElementById('edit_role'));
    modal.show();
}

// Open delete modal
function openDeleteModal(roleId) {
    document.getElementById('delete-role-id').value = roleId;
    const modal = new bootstrap.Modal(document.getElementById('delete_modal'));
    modal.show();
}

// Get status badge HTML
function getStatusBadge(status) {
    if (status === 'Active') {
        return '<span class="badge badge-soft-success">Active</span>';
    } else {
        return '<span class="badge badge-soft-danger">Inactive</span>';
    }
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
        <strong>${type === 'success' ? 'Succès!' : 'Erreur!'}</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Set loading state
function setLoadingState(loading) {
    const tbody = document.querySelector('table tbody');
    if (!tbody) return;

    if (loading) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">Chargement...</span>
                    </div>
                    <p class="text-muted mb-0 mt-2">Chargement des rôles...</p>
                </td>
            </tr>
        `;
    }
}

// Setup form validation
function setupFormValidation() {
    // Add role form validation
    const addForm = document.getElementById('add-role-form');
    if (addForm) {
        addForm.addEventListener('input', function(e) {
            clearFieldValidation(e.target);
            validateField(e.target);
        });
    }

    // Edit role form validation
    const editForm = document.getElementById('edit-role-form');
    if (editForm) {
        editForm.addEventListener('input', function(e) {
            clearFieldValidation(e.target);
            validateField(e.target);
        });
    }
}

// Validate individual field
function validateField(field) {
    if (field.name === 'name') {
        if (!field.value.trim()) {
            markFieldInvalid(field, 'Le nom du rôle est obligatoire');
            return false;
        }
        if (field.value.trim().length < 2) {
            markFieldInvalid(field, 'Le nom du rôle doit contenir au moins 2 caractères');
            return false;
        }
    }
    return true;
}

// Mark field as invalid
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

// Clear field validation
function clearFieldValidation(field) {
    field.classList.remove('is-invalid');
    const feedback = field.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.remove();
    }
}

// Clear form validation
function clearFormValidation(form) {
    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });

    const feedbacks = form.querySelectorAll('.invalid-feedback');
    feedbacks.forEach(feedback => feedback.remove());
}
