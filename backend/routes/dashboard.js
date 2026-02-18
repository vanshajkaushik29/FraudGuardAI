const express = require('express');
const Transaction = require('../models/Transaction');
const Expense = require('../models/Expense');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Apply protection to all routes
router.use(protect);

// @route   GET /api/dashboard/stats
// @desc    Get dashboard statistics
// @access  Private
router.get('/stats', async (req, res) => {
    try {
        const userId = req.user._id;

        // Get total expenses
        const expenseStats = await Expense.aggregate([
            { $match: { user: userId } },
            { $group: {
                _id: null,
                totalExpenses: { $sum: '$amount' },
                avgExpense: { $avg: '$amount' },
                count: { $sum: 1 }
            }}
        ]);

        // Get fraud statistics
        const fraudStats = await Transaction.aggregate([
            { $match: { user: userId } },
            { $group: {
                _id: null,
                totalTransactions: { $sum: 1 },
                fraudTransactions: {
                    $sum: { $cond: ['$fraudResult.isFraud', 1, 0] }
                },
                totalAmount: { $sum: '$amount' },
                fraudAmount: {
                    $sum: {
                        $cond: ['$fraudResult.isFraud', '$amount', 0]
                    }
                }
            }}
        ]);

        // Get recent expenses by category
        const categoryBreakdown = await Expense.aggregate([
            { $match: { user: userId } },
            { $group: {
                _id: '$category',
                total: { $sum: '$amount' },
                count: { $sum: 1 }
            }},
            { $sort: { total: -1 } }
        ]);

        // Get monthly trends
        const monthlyTrends = await Expense.aggregate([
            { $match: { user: userId } },
            { $group: {
                _id: {
                    year: { $year: '$date' },
                    month: { $month: '$date' }
                },
                total: { $sum: '$amount' },
                count: { $sum: 1 }
            }},
            { $sort: { '_id.year': -1, '_id.month': -1 } },
            { $limit: 6 }
        ]);

        // Get recent transactions
        const recentTransactions = await Transaction.find({ user: userId })
            .sort({ createdAt: -1 })
            .limit(5);

        // Get recent expenses
        const recentExpenses = await Expense.find({ user: userId })
            .sort({ date: -1 })
            .limit(5);

        res.json({
            success: true,
            data: {
                expenses: {
                    total: expenseStats[0]?.totalExpenses || 0,
                    average: expenseStats[0]?.avgExpense || 0,
                    count: expenseStats[0]?.count || 0
                },
                fraud: {
                    totalTransactions: fraudStats[0]?.totalTransactions || 0,
                    fraudTransactions: fraudStats[0]?.fraudTransactions || 0,
                    fraudRate: fraudStats[0]?.totalTransactions 
                        ? (fraudStats[0].fraudTransactions / fraudStats[0].totalTransactions * 100).toFixed(2)
                        : 0,
                    totalAmount: fraudStats[0]?.totalAmount || 0,
                    fraudAmount: fraudStats[0]?.fraudAmount || 0
                },
                categoryBreakdown,
                monthlyTrends,
                recentTransactions,
                recentExpenses
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({
            success: false,
            message: 'Server error'
        });
    }
});

// @route   GET /api/dashboard/recent
// @desc    Get recent activities
// @access  Private
router.get('/recent', async (req, res) => {
    try {
        const userId = req.user._id;
        const limit = parseInt(req.query.limit) || 10;

        // Get recent transactions
        const transactions = await Transaction.find({ user: userId })
            .sort({ createdAt: -1 })
            .limit(limit);

        // Get recent expenses
        const expenses = await Expense.find({ user: userId })
            .sort({ date: -1 })
            .limit(limit);

        // Combine and sort by date
        const activities = [
            ...transactions.map(t => ({
                type: 'transaction',
                data: t,
                date: t.createdAt
            })),
            ...expenses.map(e => ({
                type: 'expense',
                data: e,
                date: e.date
            }))
        ].sort((a, b) => b.date - a.date).slice(0, limit);

        res.json({
            success: true,
            data: activities
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({
            success: false,
            message: 'Server error'
        });
    }
});

module.exports = router;