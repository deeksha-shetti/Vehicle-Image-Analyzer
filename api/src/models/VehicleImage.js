const mongoose = require('mongoose');

const vehicleImageSchema = new mongoose.Schema(
  {
    processingId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    originalFilename: {
      type: String,
      required: true,
    },
    storageUrl: {
      type: String,
      required: true,
    },
    status: {
      type: String,
      enum: ['pending', 'processing', 'completed', 'failed'],
      default: 'pending',
      required: true,
      index: true,
    },
    uploadedAt: {
      type: Date,
      default: Date.now,
    },
    processedAt: {
      type: Date,
      default: null,
    },
    analysis: {
      type: mongoose.Schema.Types.Mixed,
      default: null,
    },
    errorMessage: {
      type: String,
      default: null,
    },
  },
  {
    timestamps: true,
  }
);

// Format JSON response to exclude internal MongoDB __v if needed
vehicleImageSchema.set('toJSON', {
  transform: (doc, ret) => {
    delete ret.__v;
    return ret;
  },
});

module.exports = mongoose.model('VehicleImage', vehicleImageSchema, 'vehicle_images');
