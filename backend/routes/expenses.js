const express = require('express');
const { body, validationResult } = require('express-validator');
const Expense = require('../models/Expense');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Apply protection to all routes
router.use(protect);

// @route   POST /api/expenses
// @desc    Create a new expense
// @access  Private
router.post('/', [
    body('amount').isFloat({ min: 0 }).withMessage('Amount must be a positive number'),
    body('category').isIn(['Food', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Healthcare', 'Education', 'Other']),
    body('description').optional().trim(),
    body('date').optional().isISO8601().withMessage('Valid date is required')
], async (req, res) => {
    try {
        // Check for validation errors
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                errors: errors.array()
            });
        }

        const { amount, category, description, date } = req.body;

        const expense = await Expense.create({
            user: req.user._id,
            amount,
            category,
            description,
            date: date || new Date()
        });

        res.status(201).json({
            success: true,
            data: expense
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({
            success: false,
            message: 'Server error'
        });
    }
});

// @route   GET /api/expenses
// @desc    Get all user expenses with filtering
// @access  Private
router.get('/', async (req, res) => {
    try {
        const { category, startDate, endDate, page = 1, limit = 10 } = req.query;
        
        // Build filter object
        const filter = { user: req.user._id };
        
        if (category) {
            filter.category = category;
        }
        
        if (startDate || endDate) {
            filter.date = {};
            if (startDate) filter.date.$gte = new Date(startDate);
            if (endDate) filter.date.$lte = new Date(endDate);
        }

        const skip = (parseInt(page) - 1) * parseInt(limit);

        const expenses = await Expense.find(filter)
            .sort({ date: -1 })
            .skip(skip)
            .limit(parseInt(limit));

        const total = await Expense.countDocuments(filter);

        // Get category summary
        const categorySummary = await Expense.aggregate([
            { $match: { user: req.user._id } },
            { $group: {
                _id: '$category',
                total: { $sum: '$amount' },
                count: { $sum: 1 }
            }},
            { $sort: { total: -1 } }
        ]);

        res.json({
            success: true,
            data: {
                expenses,
                categorySummary,
                pagination: {
                    page: parseInt(page),
                    limit: parseInt(limit),
                    total,
                    pages: Math.ceil(total / parseInt(limit))
                }
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

// @route   GET /api/expenses/:id
// @desc    Get single expense
// @access  Private
router.get('/:id', async (req, res) => {
    try {
        const expense = await Expense.findOne({
            _id: req.params.id,
            user: req.user._id
        });

        if (!expense) {
            return res.status(404).json({
                success: false,
                message: 'Expense not found'
            });
        }

        res.json({
            success: true,
            data: expense
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({
            success: false,
            message: 'Server error'
        });
    }
});

// @route   PUT /api/expenses/:id
// @desc    Update expense
// @access  Private
router.put('/:id', [
    body('amount').optional().isFloat({ min: 0 }),
    body('category').optional().isIn(['Food', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Healthcare', 'Education', 'Other']),
    body('description').optional().trim(),
    body('date').optional().isISO8601()
], async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                errors: errors.array()
            });
        }

        const expense = await Expense.findOneAndUpdate(
            { _id: req.params.id, user: req.user._id },
            req.body,
            { new: true, runValidators: true }
        );

        if (!expense) {
            return res.status(404).json({
                success: false,
                message: 'Expense not found'
            });
        }

        res.json({
            success: true,
            data: expense
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({
            success: false,
            message: 'Server error'
        });
    }
});

// @route   DELETE /api/expenses/:id
// @desc    Delete expense
// @access  Private
router.delete('/:id', async (req, res) => {
    try {
        const expense = await Expense.findOneAndDelete({
            _id: req.params.id,
            user: req.user._id
        });

        if (!expense) {
            return res.status(404).json({
                success: false,
                message: 'Expense not found'
            });
        }

        res.json({
            success: true,
            message: 'Expense deleted successfully'
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