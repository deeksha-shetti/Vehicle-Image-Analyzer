require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { connectDB, disconnectDB } = require('./config/db');
const { imageQueue } = require('./queues/imageQueue');
const healthRoutes = require('./routes/healthRoute');
const imageRoutes = require('./routes/imageRoutes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
const PORT = process.env.PORT || 3000;

// Connect to MongoDB
connectDB();

// Middlewares
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  console.log(`[HTTP] ${req.method} ${req.url}`);
  next();
});

// Routes
app.use('/health', healthRoutes);
app.use('/api/v1/images', imageRoutes);

// Centralized Error Handler
app.use(errorHandler);

// Start server
const server = app.listen(PORT, () => {
  console.log(`[API] Server running on port ${PORT}`);
});

// Graceful Shutdown
const gracefulShutdown = async (signal) => {
  console.log(`[API] Received ${signal}. Initiating graceful shutdown...`);
  server.close(async () => {
    console.log('[API] HTTP server closed.');
    try {
      await imageQueue.close();
      console.log('[BullMQ] Queue connection closed.');
      await disconnectDB();
      console.log('[API] Graceful shutdown completed.');
      process.exit(0);
    } catch (err) {
      console.error('[API] Error during graceful shutdown:', err);
      process.exit(1);
    }
  });
};

process.on('SIGINT', () => gracefulShutdown('SIGINT'));
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));

module.exports = app;
