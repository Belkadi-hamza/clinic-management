(function () {
    try {
        var token = localStorage.getItem('access_token');
        if (!token) {
            window.location.replace('login.html');
            return;
        }
        fetch(apiUrl('/auth/me'), { headers: { 'Authorization': 'Bearer ' + token } })
            .then(function (resp) { if (!resp.ok) throw new Error('unauth'); return resp.json(); })
            .catch(function (error) {
                // Check if it's a connection error
                if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
                    window.location.replace('error-500.html');
                } else {
                    localStorage.removeItem('access_token');
                    window.location.replace('login.html');
                }
            });
    } catch (e) {
        window.location.replace('error-500.html');
    }
})();