const express = require('express');
const router = express.Router();
const upload = require('../middlewares/upload');
const { uploadImage, getImageStatus } = require('../controllers/imageController');

router.post('/upload', upload.single('image'), uploadImage);
router.get('/:processingId', getImageStatus);

module.exports = router;
