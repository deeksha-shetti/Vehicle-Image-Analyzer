# Vehicle Image Processing System Design

This document outlines the system architecture and design for the Backend + AI Engineering take-home assignment, based on your proposed stack (Node.js/Express, Python, MongoDB, Redis/BullMQ).

## User Review Required
> [!IMPORTANT]
> Please review this system design. Once you approve this architecture, we can proceed to implement the backend API, Python worker, and Docker configuration step-by-step. Let me know if you would like to adjust the tech choices (e.g. cloud storage provider, OCR libraries).

## 1. High-Level Architecture
The system follows a standard asynchronous producer-consumer architecture:
1. **Client** interacts with a **Node.js Express API**.
2. **API** saves metadata to **MongoDB**, uploads the image to **Cloud Object Storage** (e.g., AWS S3, Cloudinary), and enqueues a job in **Redis** via **BullMQ**.
3. **Python Worker** continuously polls/listens to the Redis queue.
4. When a job is picked up, the **Worker** downloads the image, runs the OpenCV/OCR pipeline, and writes the results directly back to **MongoDB**.
5. The **Client** polls the API to retrieve the final processing status and results.

## 2. End-to-End Request/Processing Flow
1. **Upload**: Client sends `POST /api/v1/images/upload` with an image file.
2. **Pre-validation**: API validates file type, size, and presence of the file.
3. **Storage**: API uploads the image to Object Storage and gets a URL.
4. **Database Init**: API creates a `VehicleImage` document in MongoDB with status `processing`.
5. **Queueing**: API adds a job to the BullMQ `image-processing` queue with the MongoDB Document ID and Image URL.
6. **Response**: API immediately returns `202 Accepted` with the `imageId`.
7. **Processing**: Python worker receives the job, downloads the image, and executes:
   - *Dimension Validation*: Checking width/height.
   - *Blur Detection*: Laplacian variance method.
   - *Brightness Detection*: Average pixel intensity.
   - *OCR*: Extract text using EasyOCR or Tesseract.
   - *Number Plate Validation*: Regex match on the OCR text.
   - *Duplicate Detection*: Generate perceptual hash (pHash) and query MongoDB for matches.
8. **Finalization**: Worker updates the MongoDB document with the extracted data and sets status to `completed` (or `failed` if an error occurred).
9. **Status Check**: Client requests `GET /api/v1/images/:imageId` and receives the final payload.

## 3. Recommended Repository Structure
```text
/
├── api/                       # Node.js + Express backend
│   ├── src/
│   │   ├── controllers/       # Route handlers
│   │   ├── middlewares/       # Multer (upload), Error handling
│   │   ├── models/            # Mongoose schemas
│   │   ├── routes/            # API routing
│   │   ├── services/          # S3 upload, BullMQ enqueue logic
│   │   └── index.js           # Express app entry point
│   ├── package.json
│   └── Dockerfile
├── worker/                    # Python background worker
│   ├── src/
│   │   ├── main.py            # BullMQ worker initialization
│   │   ├── image_pipeline.py  # OpenCV and OCR logic
│   │   ├── db.py              # MongoDB connection & updates
│   │   └── config.py          # Environment configuration
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml         # Local dev orchestration
├── .env.example
└── README.md
```

## 4. MongoDB Schema
**Collection: `vehicle_images`**
```json
{
  "_id": "ObjectId",
  "originalFilename": "string",
  "storageUrl": "string",
  "status": "string", // Enum: ['pending', 'processing', 'completed', 'failed']
  "uploadedAt": "Date",
  "processedAt": "Date",
  "analysis": {
    "dimensions": {
      "width": "number",
      "height": "number"
    },
    "isBlurred": "boolean",
    "blurScore": "number",
    "isDark": "boolean",
    "brightnessScore": "number",
    "ocrText": "string",
    "hasValidIndianNumberPlate": "boolean",
    "isDuplicate": "boolean",
    "imageHash": "string" // Perceptual hash for duplicate detection
  },
  "errorMessage": "string" // Populated if status is 'failed'
}
```

## 5. API Endpoint Contracts

### `POST /api/v1/images/upload`
- **Content-Type**: `multipart/form-data`
- **Body**: `image` (file)
- **Response (202 Accepted)**:
```json
{
  "message": "Image uploaded and queued for processing.",
  "imageId": "60d5ec49f3b5a1234567890a",
  "status": "processing"
}
```

### `GET /api/v1/images/:imageId`
- **Response (200 OK) - Processing Complete**:
```json
{
  "imageId": "60d5ec49f3b5a1234567890a",
  "status": "completed",
  "uploadedAt": "2023-10-27T10:00:00Z",
  "results": {
    "dimensions": { "width": 1920, "height": 1080 },
    "isBlurred": false,
    "blurScore": 145.2,
    "isDark": false,
    "brightnessScore": 120.5,
    "ocrText": "MH12AB1234",
    "hasValidIndianNumberPlate": true,
    "isDuplicate": false
  }
}
```

## 6. BullMQ Job Structure
When the API pushes to Redis, the job payload will look like this:
```json
{
  "name": "process-vehicle-image",
  "data": {
    "imageId": "60d5ec49f3b5a1234567890a",
    "storageUrl": "https://your-bucket.s3.region.amazonaws.com/uuid-image.jpg"
  },
  "opts": {
    "attempts": 3,
    "backoff": {
      "type": "exponential",
      "delay": 2000
    }
  }
}
```

## 7. API ↔ Redis ↔ Worker Communication
- **BullMQ Cross-Language Support**: BullMQ is primarily a Node.js library, but there is a compatible Python library (`bullmq` pip package) that allows Python workers to consume BullMQ jobs perfectly.
- **State Updates**: The worker updates the MongoDB document directly rather than sending a message back to the Node API. This keeps the architecture simple and decoupled.

## 8. Failure and Retry Strategy
- **Transient Failures (e.g., Network, Cloud Storage timeout)**: BullMQ is configured with `attempts: 3` and an exponential backoff. The worker will automatically retry.
- **Permanent Failures (e.g., Corrupt image)**: If all retries fail, the job is moved to BullMQ's "Failed" state. The worker will catch the final exception and update the MongoDB document `status` to `failed`, populating the `errorMessage` field.

## 9. Required Environment Variables
```env
# Shared
MONGODB_URI=mongodb+srv://...
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API Specific
PORT=3000
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
AWS_S3_BUCKET_NAME=

# Worker Specific
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata # If using Tesseract
```

## 10. Docker Architecture (Local Development)
We will use a `docker-compose.yml` to spin up the entire stack locally:
- `api`: Node.js container built from `./api/Dockerfile`.
- `worker`: Python container built from `./worker/Dockerfile` (includes OpenCV and OCR dependencies).
- `redis`: Standard `redis:alpine` image.
- `mongodb`: Standard `mongo:latest` image.

## 11. Deployment Architecture (Suitable for a 36-hour Take-Home)
To minimize infrastructure setup time while demonstrating production readiness:
- **Hosting Platform**: Use **Render** or **Railway**. Both easily support deploying `docker-compose` setups or separate Git repositories via Dockerfiles.
- **Managed Databases**:
  - **MongoDB Atlas**: Free tier for MongoDB.
  - **Upstash** or **Render Redis**: Managed Redis instance.
- **Object Storage**: AWS S3 or **Cloudinary** (Cloudinary often has an easier setup/free tier for hackathons and take-homes).

## 12. Important Security and Validation Considerations
> [!WARNING]
> Implementing these will show attention to detail and production readiness.
1. **API Upload Validation**: Use `multer` to enforce file size limits (e.g., max 5MB) and mime types (`image/jpeg`, `image/png`). Reject unexpected files early.
2. **Sanitization**: Trim and sanitize the OCR text before saving it to the database to prevent basic injection vectors.
3. **Graceful Shutdown**: Both Node.js and Python worker must handle `SIGINT`/`SIGTERM` to cleanly close Redis and MongoDB connections, avoiding dangling jobs.
4. **Idempotency**: Duplicate detection relies on Image Hashing (pHash). If a user uploads the exact same image, the worker should gracefully flag it as `isDuplicate: true` rather than crashing or throwing unhandled database errors.
