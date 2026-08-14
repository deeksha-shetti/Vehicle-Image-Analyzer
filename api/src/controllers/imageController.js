const { v4: uuidv4, validate: uuidValidate } = require('uuid');
const VehicleImage = require('../models/VehicleImage');
const { uploadToCloudinary } = require('../services/storageService');
const { addImageProcessingJob } = require('../queues/imageQueue');

const uploadImage = async (req, res, next) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image file provided. Please attach an image file.' });
    }

    const processingId = uuidv4();
    console.log(`[ImageController] Processing upload request with processingId: ${processingId}`);

    // Upload to Cloudinary
    const storageUrl = await uploadToCloudinary(req.file.buffer, 'vehicle_images');

    // Create MongoDB document with initial status "pending"
    const vehicleImage = await VehicleImage.create({
      processingId,
      originalFilename: req.file.originalname,
      storageUrl,
      status: 'pending',
      uploadedAt: new Date(),
    });

    // Queue processing job in BullMQ
    await addImageProcessingJob(processingId, storageUrl);

    return res.status(202).json({
      message: 'Image uploaded and queued for processing.',
      processingId: vehicleImage.processingId,
      status: vehicleImage.status,
    });
  } catch (error) {
    next(error);
  }
};

const getImageStatus = async (req, res, next) => {
  try {
    const { processingId } = req.params;

    if (!processingId || !uuidValidate(processingId)) {
      return res.status(400).json({ error: 'Invalid processingId format. Must be a valid UUID.' });
    }

    const vehicleImage = await VehicleImage.findOne({ processingId });

    if (!vehicleImage) {
      return res.status(404).json({ error: 'Image processing record not found for the provided processingId.' });
    }

    return res.status(200).json({
      processingId: vehicleImage.processingId,
      originalFilename: vehicleImage.originalFilename,
      storageUrl: vehicleImage.storageUrl,
      status: vehicleImage.status,
      uploadedAt: vehicleImage.uploadedAt,
      processedAt: vehicleImage.processedAt,
      analysis: vehicleImage.analysis,
      errorMessage: vehicleImage.errorMessage,
    });
  } catch (error) {
    next(error);
  }
};

module.exports = {
  uploadImage,
  getImageStatus,
};
