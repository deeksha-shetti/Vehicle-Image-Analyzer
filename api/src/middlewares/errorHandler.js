const multer = require('multer');

const errorHandler = (err, req, res, next) => {
  console.error(`[Error] ${err.message}`, err);

  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        error: 'File size exceeds maximum limit of 5MB.',
      });
    }
    return res.status(400).json({
      error: `Upload error: ${err.message}`,
    });
  }

  const statusCode = err.status || err.statusCode || 500;
  const message = err.message || 'Internal Server Error';

  res.status(statusCode).json({
    error: message,
  });
};

module.exports = errorHandler;
