// Show/hide tabs
function showTab(tabName) {
    const tabs = document.querySelectorAll('.tab-btn');
    const forms = document.querySelectorAll('.auth-form');
    
    tabs.forEach(tab => {
        if (tab.textContent.toLowerCase().includes(tabName)) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    forms.forEach(form => {
        if (form.id.includes(tabName)) {
            form.classList.add('active');
        } else {
            form.classList.remove('active');
        }
    });
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const result = await login(email, password);
        
        if (result.success) {
            window.location.href = '/dashboard.html';
        } else {
            alert(result.message || 'Login failed');
        }
    } catch (error) {
        alert(error.message);
    }
}

// Handle register
async function handleRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    if (password.length < 6) {
        alert('Password must be at least 6 characters long');
        return;
    }
    
    try {
        const result = await register(name, email, password);
        
        if (result.success) {
            alert('Registration successful! Please login.');
            showTab('login');
        } else {
            alert(result.message || 'Registration failed');
        }
    } catch (error) {
        alert(error.message);
    }
}

// Check if already logged in
if (isAuthenticated() && window.location.pathname.endsWith('index.html')) {
    window.location.href = '/dashboard.html';
}