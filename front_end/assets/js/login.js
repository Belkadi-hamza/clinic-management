// Vérifie si l'utilisateur est déjà connecté
window.addEventListener('DOMContentLoaded', function () {
    const token = localStorage.getItem('access_token');
    if (token) {
        // Vérifie si le jeton est encore valide et redirige si c’est le cas
        fetch(apiUrl('/auth/me'), {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(response => {
                if (response.ok) {
                    showSuccess('Bon retour ! Redirection vers votre tableau de bord...');
                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 1000);
                } else {
                    // Jeton invalide, on le supprime
                    localStorage.removeItem('access_token');
                    showInfo('Votre session a expiré. Veuillez vous reconnecter.');
                }
            })
            .catch(error => {
                console.log('Échec de la vérification du jeton :', error);
                localStorage.removeItem('access_token');

                // Vérifie s’il s’agit d’une erreur de connexion
                if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
                    showError('Impossible de se connecter au serveur. Veuillez vérifier votre connexion Internet et réessayer.', true);
                } else {
                    showInfo('Échec de la vérification de la session. Veuillez vous reconnecter.');
                }
            });
    }
});

document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!username || !password) {
        showError('Veuillez saisir à la fois le nom d’utilisateur et le mot de passe pour continuer.');
        return;
    }

    hideMessages();
    setFormLoading(true);

    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(apiUrl('/auth/token'), {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Enregistre le jeton
            localStorage.setItem('access_token', data.access_token);

            // Enregistre les infos de l’utilisateur pour la personnalisation
            if (data.user) {
                localStorage.setItem('user_name', `${data.user.first_name} ${data.user.last_name}`);
                localStorage.setItem('user_role', data.user.role);
            }

            showSuccess(`Bon retour, ${data.user?.first_name || username} ! Redirection vers votre tableau de bord...`);

            // Effet de transition douce
            const mainWrapper = document.querySelector('.main-wrapper');
            if (mainWrapper) mainWrapper.style.opacity = '0.7';

            // Redirige vers l’application principale après un court délai
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
        } else {
            let errorMessage = 'Échec de la connexion. ';

            // Messages d’erreur conviviaux selon la réponse
            if (response.status === 401) {
                if (data.detail?.includes('Invalid username or password')) {
                    errorMessage += 'Le nom d’utilisateur ou le mot de passe est incorrect. Veuillez réessayer.';
                } else if (data.detail?.includes('Account is deactivated')) {
                    errorMessage += 'Votre compte a été désactivé. Veuillez contacter votre administrateur.';
                } else {
                    errorMessage += 'Veuillez vérifier vos identifiants et réessayer.';
                }
            } else if (response.status === 400) {
                errorMessage += 'Veuillez vérifier vos informations et réessayer.';
            } else if (response.status >= 500) {
                errorMessage += 'Nos serveurs rencontrent des problèmes. Veuillez réessayer dans quelques instants.';
            } else {
                errorMessage += data.detail || 'Veuillez réessayer.';
            }

            showError(errorMessage);
        }
    } catch (error) {
        console.error('Erreur de connexion :', error);

        let errorMessage = 'Erreur réseau. ';
        errorMessage += 'Veuillez vérifier votre connexion et réessayer.';
        showError(errorMessage);
    } finally {
        setFormLoading(false);
    }
});

function showError(message, showRetry = false) {
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');

    errorMessage.innerHTML = message;
    errorAlert.style.display = 'block';
    errorAlert.classList.add('show');

    // Ajoute un bouton de réessai pour les erreurs de connexion
    if (showRetry) {
        if (!document.getElementById('retryButton')) {
            const retryButton = document.createElement('button');
            retryButton.id = 'retryButton';
            retryButton.className = 'btn btn-sm btn-outline-light mt-2';
            retryButton.innerHTML = '<i class="ti ti-refresh me-1"></i> Réessayer';
            retryButton.onclick = () => window.location.reload();
            errorAlert.appendChild(retryButton);
        }
    } else {
        const retryButton = document.getElementById('retryButton');
        if (retryButton) retryButton.remove();
    }

    // Masque automatiquement après 8 secondes pour les erreurs non critiques
    if (!showRetry) {
        setTimeout(() => {
            errorAlert.style.display = 'none';
        }, 8000);
    }
}

function showSuccess(message) {
    const successAlert = document.getElementById('successAlert');
    const successMessage = document.getElementById('successMessage');

    successMessage.textContent = message;
    successAlert.style.display = 'block';
    successAlert.classList.add('show');

    // Masque automatiquement après 4 secondes (l’utilisateur sera redirigé)
    setTimeout(() => {
        successAlert.style.display = 'none';
    }, 4000);
}

function hideMessages() {
    const errorAlert = document.getElementById('errorAlert');
    const successAlert = document.getElementById('successAlert');

    if (errorAlert) {
        errorAlert.style.display = 'none';
        errorAlert.classList.remove('show');
    }
    if (successAlert) {
        successAlert.style.display = 'none';
        successAlert.classList.remove('show');
    }
}

function setFormLoading(loading) {
    const loginBtn = document.getElementById('loginBtn');
    const loginText = document.getElementById('loginText');
    const loginSpinner = document.getElementById('loginSpinner');

    if (loading) {
        loginBtn.disabled = true;
        loginText.textContent = 'Connexion en cours...';
        loginSpinner.style.display = 'inline-block';
    } else {
        loginBtn.disabled = false;
        loginText.textContent = 'Se connecter';
        loginSpinner.style.display = 'none';
    }
}

// Ajoute la prise en charge de la touche Entrée
document.addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !document.getElementById('loginBtn').disabled) {
        document.getElementById('loginForm').dispatchEvent(new Event('submit'));
    }
});

// Ajoute des écouteurs d’événements pour effacer les erreurs lorsque l’utilisateur commence à taper
document.getElementById('username').addEventListener('input', hideMessages);
document.getElementById('password').addEventListener('input', hideMessages);