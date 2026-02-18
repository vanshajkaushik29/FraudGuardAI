const mongoose = require('mongoose');

const transactionSchema = new mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    amount: {
        type: Number,
        required: [true, 'Please provide amount'],
        min: [0, 'Amount cannot be negative']
    },
    location: {
        type: String,
        required: [true, 'Please provide location'],
        trim: true
    },
    time: {
        type: Date,
        required: [true, 'Please provide time'],
        default: Date.now
    },
    fraudResult: {
        isFraud: {
            type: Boolean,
            default: false
        },
        confidence: {
            type: Number,
            min: 0,
            max: 1
        },
        checkedAt: {
            type: Date,
            default: Date.now
        }
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Transaction', transactionSchema);