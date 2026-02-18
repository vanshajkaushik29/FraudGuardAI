// Check authentication
if (!isAuthenticated()) {
    window.location.href = '/';
}

// Current user
const currentUser = getCurrentUser();
if (currentUser) {
    document.getElementById('user-name').textContent = `Welcome, ${currentUser.name}`;
}

// Current section
let currentSection = 'overview';
let currentPage = {
    transactions: 1,
    expenses: 1
};

// Show section
function showSection(sectionId) {
    // Update menu
    document.querySelectorAll('.sidebar-menu li').forEach(item => {
        if (item.textContent.toLowerCase().includes(sectionId.replace('-', ' '))) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Update section
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
    
    // Load section data
    switch(sectionId) {
        case 'overview':
            loadDashboardStats();
            break;
        case 'transactions':
            loadTransactions();
            break;
        case 'expenses':
            loadExpenses();
            break;
        case 'fraud-alerts':
            loadFraudAlerts();
            break;
    }
    
    currentSection = sectionId;
}

// Load dashboard stats
async function loadDashboardStats() {
    try {
        const result = await getDashboardStats();
        
        if (result.success) {
            renderDashboardStats(result.data);
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

// Render dashboard stats
function renderDashboardStats(data) {
    const statsHtml = `
        <div class="stat-card">
            <h3>Total Expenses</h3>
            <div class="value">₹${data.expenses.total.toFixed(2)}</div>
        </div>
        <div class="stat-card">
            <h3>Average Expense</h3>
            <div class="value">₹${data.expenses.average.toFixed(2)}</div>
        </div>
        <div class="stat-card warning">
            <h3>Fraud Transactions</h3>
            <div class="value">${data.fraud.fraudTransactions}</div>
            <small>${data.fraud.fraudRate}% fraud rate</small>
        </div>
        <div class="stat-card">
            <h3>Total Transactions</h3>
            <div class="value">${data.fraud.totalTransactions}</div>
        </div>
    `;
    
    document.getElementById('dashboard-stats').innerHTML = statsHtml;
    
    // Render charts
    renderCategoryChart(data.categoryBreakdown);
    renderTrendsChart(data.monthlyTrends);
    renderRecentActivity([...data.recentTransactions, ...data.recentExpenses]);
}

// Render category chart
function renderCategoryChart(categories) {
    const container = document.getElementById('category-chart');
    let html = '<div style="width: 100%;">';
    
    const maxTotal = Math.max(...categories.map(c => c.total), 1);
    
    categories.forEach(cat => {
        const percentage = (cat.total / maxTotal * 100) || 0;
        html += `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between;">
                    <span>${cat._id}</span>
                    <span>₹${cat.total.toFixed(2)}</span>
                </div>
                <div style="background: #edf2f7; height: 20px; border-radius: 10px;">
                    <div style="background: #667eea; width: ${percentage}%; height: 100%; border-radius: 10px;"></div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Render trends chart
function renderTrendsChart(trends) {
    const container = document.getElementById('trends-chart');
    
    if (!trends || trends.length === 0) {
        container.innerHTML = '<p>No data available</p>';
        return;
    }
    
    let html = '<div style="display: flex; align-items: flex-end; height: 200px; gap: 20px;">';
    
    const maxTotal = Math.max(...trends.map(t => t.total), 1);
    
    trends.reverse().forEach(trend => {
        const height = (trend.total / maxTotal * 180) || 0;
        const monthName = new Date(trend._id.year, trend._id.month - 1).toLocaleString('default', { month: 'short' });
        
        html += `
            <div style="flex: 1; text-align: center;">
                <div style="background: #667eea; height: ${height}px; border-radius: 5px 5px 0 0;"></div>
                <div style="margin-top: 5px;">${monthName}</div>
                <div style="font-size: 12px;">₹${trend.total.toFixed(0)}</div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Render recent activity
function renderRecentActivity(activities) {
    const container = document.getElementById('recent-activity-list');
    
    if (!activities.length) {
        container.innerHTML = '<p>No recent activity</p>';
        return;
    }
    
    let html = '';
    activities.slice(0, 5).forEach(activity => {
        if (activity.type === 'transaction') {
            html += `
                <div class="activity-item ${activity.data.fraudResult?.isFraud ? 'fraud' : ''}">
                    <div>
                        <strong>Transaction</strong>
                        <div>Amount: ₹${activity.data.amount}</div>
                        <div>Location: ${activity.data.location}</div>
                    </div>
                    <div>
                        ${activity.data.fraudResult?.isFraud ? 
                            '<span style="color: #f56565;">⚠️ Fraud Detected</span>' : 
                            '<span style="color: #48bb78;">✓ Safe</span>'}
                    </div>
                    <div>${new Date(activity.data.createdAt).toLocaleDateString()}</div>
                </div>
            `;
        } else {
            html += `
                <div class="activity-item">
                    <div>
                        <strong>Expense</strong>
                        <div>Amount: ₹${activity.data.amount}</div>
                        <div>Category: ${activity.data.category}</div>
                    </div>
                    <div>${activity.data.description || ''}</div>
                    <div>${new Date(activity.data.date).toLocaleDateString()}</div>
                </div>
            `;
        }
    });
    
    container.innerHTML = html;
}

// Load transactions
async function loadTransactions(page = 1) {
    try {
        const result = await getTransactions(page);
        
        if (result.success) {
            renderTransactions(result.data.transactions);
            renderPagination('transactions', result.data.pagination);
        }
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

// Render transactions
function renderTransactions(transactions) {
    const container = document.getElementById('transactions-list');
    
    if (!transactions.length) {
        container.innerHTML = '<p style="padding: 20px; text-align: center;">No transactions found</p>';
        return;
    }
    
    let html = '';
    transactions.forEach(t => {
        html += `
            <div class="transaction-item ${t.fraudResult?.isFraud ? 'fraud' : ''}">
                <div>
                    <strong>Amount: ₹${t.amount}</strong>
                    <div>Location: ${t.location}</div>
                </div>
                <div>
                    <div>${new Date(t.time).toLocaleString()}</div>
                    ${t.fraudResult?.isFraud ? 
                        '<span style="color: #f56565; font-weight: bold;">FRAUD ALERT</span>' : 
                        '<span style="color: #48bb78;">Legitimate</span>'}
                </div>
                <div>
                    <small>Confidence: ${(t.fraudResult?.confidence * 100).toFixed(1)}%</small>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Load expenses
async function loadExpenses(page = 1) {
    try {
        const category = document.getElementById('expense-category-filter')?.value || '';
        const startDate = document.getElementById('expense-start-date')?.value || '';
        const endDate = document.getElementById('expense-end-date')?.value || '';
        
        const result = await getExpenses(category, startDate, endDate, page);
        
        if (result.success) {
            renderExpenses(result.data.expenses);
            renderPagination('expenses', result.data.pagination);
        }
    } catch (error) {
        console.error('Error loading expenses:', error);
    }
}

// Render expenses
function renderExpenses(expenses) {
    const container = document.getElementById('expenses-list');
    
    if (!expenses.length) {
        container.innerHTML = '<p style="padding: 20px; text-align: center;">No expenses found</p>';
        return;
    }
    
    let html = '';
    expenses.forEach(e => {
        html += `
            <div class="expense-item">
                <div>
                    <strong>₹${e.amount}</strong>
                    <div>${e.category}</div>
                </div>
                <div>
                    <div>${e.description || 'No description'}</div>
                </div>
                <div>
                    <div>${new Date(e.date).toLocaleDateString()}</div>
                    <button onclick="deleteExpenseItem('${e._id}')" class="btn-secondary" style="background: #f56565; padding: 4px 8px; font-size: 12px;">Delete</button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Load fraud alerts
async function loadFraudAlerts() {
    try {
        const result = await getFraudTransactions();
        
        if (result.success) {
            renderFraudAlerts(result.data);
        }
    } catch (error) {
        console.error('Error loading fraud alerts:', error);
    }
}

// Render fraud alerts
function renderFraudAlerts(transactions) {
    const container = document.getElementById('fraud-alerts-list');
    
    if (!transactions.length) {
        container.innerHTML = '<p style="padding: 20px; text-align: center;">No fraud alerts found</p>';
        return;
    }
    
    let html = '';
    transactions.forEach(t => {
        html += `
            <div class="fraud-item">
                <div>
                    <strong>⚠️ Fraudulent Transaction</strong>
                    <div>Amount: ₹${t.amount}</div>
                    <div>Location: ${t.location}</div>
                </div>
                <div>
                    <div>Time: ${new Date(t.time).toLocaleString()}</div>
                    <div>Detected: ${new Date(t.fraudResult.checkedAt).toLocaleString()}</div>
                </div>
                <div>
                    <small>Confidence: ${(t.fraudResult.confidence * 100).toFixed(1)}%</small>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Render pagination
function renderPagination(type, pagination) {
    const container = document.getElementById(`${type}-pagination`);
    
    if (!container) return;
    
    let html = '';
    for (let i = 1; i <= pagination.pages; i++) {
        html += `
            <button class="${i === pagination.page ? 'active' : ''}" 
                    onclick="${type === 'transactions' ? 'loadTransactions' : 'loadExpenses'}(${i})">
                ${i}
            </button>
        `;
    }
    
    container.innerHTML = html;
}

// Handle add transaction
// Handle add transaction
// Handle add transaction
// Handle add transaction
async function handleAddTransaction(event) {
    event.preventDefault();
    
    const amount = document.getElementById('transaction-amount').value;
    const location = document.getElementById('transaction-location').value;
    const timeInput = document.getElementById('transaction-time').value;
    
    if (!timeInput) {
        alert('Please select date and time');
        return;
    }
    
    // Fix timezone issue - keep the exact time selected
    const selectedDate = new Date(timeInput);
    // Don't adjust for timezone - send the local time as-is
    const timeISO = selectedDate.toISOString();
    
    console.log('Original input:', timeInput);
    console.log('Selected date:', selectedDate.toString());
    console.log('Sending ISO:', timeISO);
    
    try {
        const result = await createTransaction(parseFloat(amount), location, timeISO);
        console.log('Transaction result:', result);
        
        if (result.success) {
            const fraudResult = document.getElementById('fraud-result');
            fraudResult.style.display = 'block';
            
            if (result.data.fraudAlert) {
                fraudResult.className = 'fraud-result fraud';
                fraudResult.innerHTML = `
                    <h3>⚠️ FRAUD ALERT!</h3>
                    <p>This transaction has been flagged as potentially fraudulent.</p>
                    <p>Amount: ₹${amount}</p>
                    <p>Confidence: ${(result.data.transaction.fraudResult.confidence * 100).toFixed(1)}%</p>
                `;
            } else {
                fraudResult.className = 'fraud-result safe';
                fraudResult.innerHTML = `
                    <h3>✓ Transaction Safe</h3>
                    <p>This transaction appears to be legitimate.</p>
                    <p>Amount: ₹${amount}</p>
                    <p>Confidence: ${(result.data.transaction.fraudResult.confidence * 100).toFixed(1)}%</p>
                `;
            }
            
            // Reset form
            event.target.reset();
            
            // Refresh data if on overview
            if (currentSection === 'overview') {
                loadDashboardStats();
            }
        }
    } catch (error) {
        console.error('Error creating transaction:', error);
        alert('Error creating transaction: ' + error.message);
    }
}
// Handle add expense
async function handleAddExpense(event) {
    event.preventDefault();
    
    const amount = document.getElementById('expense-amount').value;
    const category = document.getElementById('expense-category').value;
    const description = document.getElementById('expense-description').value;
    const date = new Date(document.getElementById('expense-date').value).toISOString();
    
    try {
        const result = await createExpense(amount, category, description, date);
        
        if (result.success) {
            alert('Expense added successfully!');
            event.target.reset();
            
            // Refresh data if on overview
            if (currentSection === 'overview') {
                loadDashboardStats();
            }
        }
    } catch (error) {
        alert('Error adding expense: ' + error.message);
    }
}

// Delete expense
async function deleteExpenseItem(id) {
    if (!confirm('Are you sure you want to delete this expense?')) return;
    
    try {
        const result = await deleteExpense(id);
        
        if (result.success) {
            loadExpenses(currentPage.expenses);
            if (currentSection === 'overview') {
                loadDashboardStats();
            }
        }
    } catch (error) {
        alert('Error deleting expense: ' + error.message);
    }
}

// Search transactions
document.getElementById('transaction-search')?.addEventListener('input', (e) => {
    // Implement search functionality
    console.log('Searching:', e.target.value);
});

// Logout
function logout() {
    // Clear token and redirect
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// Load initial data
document.addEventListener('DOMContentLoaded', () => {
    showSection('overview');
});