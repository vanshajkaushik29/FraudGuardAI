// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';
let authToken = localStorage.getItem('token');

// Helper function for API calls

async function apiCall(endpoint, method = 'GET', data = null) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const headers = {
        'Content-Type': 'application/json',
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const options = {
        method,
        headers,
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        console.log(`Making ${method} request to ${url}`, data);
        const response = await fetch(url, options);
        
        // Try to get response body even if not OK
        const responseText = await response.text();
        console.log('Response status:', response.status);
        console.log('Response body:', responseText);
        
        let result;
        try {
            result = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse JSON response:', responseText);
            throw new Error('Invalid JSON response from server');
        }
        
        if (!response.ok) {
            throw new Error(result.message || `API call failed with status ${response.status}`);
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}
// Auth APIs
async function register(name, email, password) {
    return apiCall('/auth/register', 'POST', { name, email, password });
}

async function login(email, password) {
    const result = await apiCall('/auth/login', 'POST', { email, password });
    if (result.token) {
        authToken = result.token;
        localStorage.setItem('token', result.token);
        localStorage.setItem('user', JSON.stringify(result.user));
    }
    return result;
}

function logout() {
    authToken = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Transaction APIs


// Transaction APIs
async function createTransaction(amount, location, time) {
    // If time is already an ISO string, use it directly
    const data = {
        amount: parseFloat(amount),
        location: location,
        time: time  // Now we're passing the ISO string directly
    };
    console.log('API call with data:', data);
    return apiCall('/transactions', 'POST', data);
}
async function getTransactions(page = 1, limit = 10) {
    return apiCall(`/transactions?page=${page}&limit=${limit}`);
}

async function getFraudTransactions() {
    return apiCall('/transactions/fraud');
}

// Expense APIs
async function createExpense(amount, category, description, date) {
    return apiCall('/expenses', 'POST', { amount, category, description, date });
}

async function getExpenses(category = '', startDate = '', endDate = '', page = 1, limit = 10) {
    let url = `/expenses?page=${page}&limit=${limit}`;
    if (category) url += `&category=${category}`;
    if (startDate) url += `&startDate=${startDate}`;
    if (endDate) url += `&endDate=${endDate}`;
    return apiCall(url);
}

async function updateExpense(id, data) {
    return apiCall(`/expenses/${id}`, 'PUT', data);
}

async function deleteExpense(id) {
    return apiCall(`/expenses/${id}`, 'DELETE');
}

// Dashboard APIs
async function getDashboardStats() {
    return apiCall('/dashboard/stats');
}

async function getRecentActivities(limit = 10) {
    return apiCall(`/dashboard/recent?limit=${limit}`);
}

// Check if user is authenticated
function isAuthenticated() {
    return !!authToken;
}

// Get current user
function getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}