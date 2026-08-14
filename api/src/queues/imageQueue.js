const { Queue } = require('bullmq');
const redisConfig = require('../config/redis');

const queueName = process.env.QUEUE_NAME || 'image-processing';

const imageQueue = new Queue(queueName, {
  connection: redisConfig,
});

const addImageProcessingJob = async (processingId, storageUrl) => {
  const job = await imageQueue.add(
    'process-vehicle-image',
    {
      processingId,
      storageUrl,
    },
    {
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 1000,
      },
      removeOnComplete: false,
      removeOnFail: false,
    }
  );
  console.log(`[BullMQ] Enqueued job ${job.id} for processingId: ${processingId}`);
  return job;
};

module.exports = {
  imageQueue,
  addImageProcessingJob,
};
