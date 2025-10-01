// login.js
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('auth_token', data.token);
            window.location.href = '/dashboard';
        } else {
            alert('Identifiants incorrects');
        }
    } catch (error) {
        console.error('Erreur login:', error);
        alert('Erreur de connexion');
    }
}