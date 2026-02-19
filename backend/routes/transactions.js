const express = require('express');
const axios = require('axios');
const { body, validationResult } = require('express-validator');
const Transaction = require('../models/Transaction');
const { protect } = require('../middleware/auth');

const router = express.Router();

// Apply protection to all routes
router.use(protect);

// @route   POST /api/transactions
// @desc    Create a new transaction and check for fraud
// @access  Private
router.post('/', [
    body('amount').isFloat({ min: 0 }).withMessage('Amount must be a positive number'),
    body('location').notEmpty().withMessage('Location is required'),
    body('time').isISO8601().withMessage('Valid date is required'),
    body('description').optional().isString().trim()
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

        const { amount, location, time, description = '' } = req.body;

        // Call AI service for fraud detection
        let fraudResult = { 
            isFraud: false, 
            confidence: 0,
            description_analysis: {},
            reasons: []
        };
        
        try {
            console.log('Calling AI service with:', { amount, location, time, description });
            
            const aiResponse = await axios.post(`${process.env.AI_SERVICE_URL}/predict`, {
                amount: parseFloat(amount),
                location,
                time: new Date(time).getTime(),
                description
            });
            
            console.log('AI Response:', aiResponse.data);
            
            fraudResult = {
                isFraud: aiResponse.data.fraud,
                confidence: aiResponse.data.confidence || 0.5,
                description_analysis: aiResponse.data.description_analysis || {},
                reasons: aiResponse.data.description_analysis?.reasons || [],
                checkedAt: new Date()
            };
            
        } catch (aiError) {
            console.error('AI service error:', aiError.message);
            // Continue with default fraud result if AI service fails
        }

        // Create transaction
        const transaction = await Transaction.create({
            user: req.user._id,
            amount,
            location,
            description,
            time,
            fraudResult
        });

        res.status(201).json({
            success: true,
            data: {
                transaction,
                fraudAlert: fraudResult.isFraud
            }
        });
        
    } catch (error) {
        console.error('Server error:', error);
        res.status(500).json({
            success: false,
            message: 'Server error'
        });
    }
});

// @route   GET /api/transactions
// @desc    Get all user transactions
// @access  Private
router.get('/', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const skip = (page - 1) * limit;

        const transactions = await Transaction.find({ user: req.user._id })
            .sort({ createdAt: -1 })
            .skip(skip)
            .limit(limit);

        const total = await Transaction.countDocuments({ user: req.user._id });

        res.json({
            success: true,
            data: {
                transactions,
                pagination: {
                    page,
                    limit,
                    total,
                    pages: Math.ceil(total / limit)
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

// @route   GET /api/transactions/fraud
// @desc    Get all fraudulent transactions
// @access  Private
router.get('/fraud', async (req, res) => {
    try {
        const fraudTransactions = await Transaction.find({
            user: req.user._id,
            'fraudResult.isFraud': true
        }).sort({ createdAt: -1 });

        res.json({
            success: true,
            data: fraudTransactions
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