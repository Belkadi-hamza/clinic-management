// Load user information on page load
window.addEventListener('DOMContentLoaded', function () {
    const token = localStorage.getItem('access_token');
    if (token) {
        // Fetch user information
        fetch(apiUrl('/auth/me'), {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Failed to fetch user info');
                }
            })
            .then(user => {
                // Update user information in the header
                document.getElementById('userFullName').textContent = user.full_name || user.first_name + ' ' + user.last_name || 'User';
                document.getElementById('userRole').textContent = user.role || 'User';

                // Optional: Update avatar if user has profile image
                if (user.profile_image) {
                    document.getElementById('userAvatar').src = user.profile_image;
                }
            })
            .catch(error => {
                console.error('Error fetching user info:', error);
                // Check if it's a connection error
                if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
                    window.location.replace('error-500.html');
                } else {
                    // Set default values if fetch fails
                    document.getElementById('userFullName').textContent = 'User';
                    document.getElementById('userRole').textContent = 'Guest';
                }
            });
    }
});

// Logout functionality
document.getElementById('logoutBtn').addEventListener('click', function (e) {
    e.preventDefault();

    const token = localStorage.getItem('access_token');

    // Remove the access token from localStorage
    localStorage.removeItem('access_token');

    // Optional: Call logout endpoint if your backend has one
    if (token) {
        fetch(apiUrl('/auth/logout'), {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token
            }
        }).catch(err => console.log('Logout endpoint not available'));
    }

    // Redirect to login page
    window.location.href = 'login.html';
});

// Add this function to your existing header.js
function updateHeaderInfo() {
    const token = localStorage.getItem('access_token');
    if (token) {
        // Re-fetch user information and update header
        fetch(apiUrl('/auth/me'), {
            headers: {
                'Authorization': 'Bearer ' + token
            }
        })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Failed to fetch user info');
                }
            })
            .then(user => {
                // Update user information in the header
                document.getElementById('userFullName').textContent = user.full_name || user.first_name + ' ' + user.last_name || 'User';
                document.getElementById('userRole').textContent = user.role || 'User';
            })
            .catch(error => {
                console.error('Error updating header info:', error);
            });
    }
}

// Load header when DOM is ready
document.addEventListener('DOMContentLoaded', loadHeader);