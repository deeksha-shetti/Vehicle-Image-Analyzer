# Vehicle Image Processing System

An asynchronous vehicle image analysis system built with Node.js/Express, MongoDB, Redis, BullMQ, Cloudinary, and Python.

## Architecture

- **API Service**: Express API handling image uploads, MongoDB persistence, Cloudinary upload, and queuing processing jobs via BullMQ.
- **Worker Service**: Python background worker processing jobs asynchronously.
- **Redis**: Job queue broker.
- **MongoDB**: Metadata and processing results store.
- **Cloudinary**: Cloud image storage.

## Setup & Running

### Environment Variables
Copy `.env.example` to `.env` and fill in your Cloudinary credentials:
```bash
cp .env.example .env
```

### Docker Compose
Run the full stack with Docker Compose:
```bash
docker-compose up --build
```

### API Endpoints
- `GET /health` - Health check endpoint
- `POST /api/v1/images/upload` - Upload image file (`image` field, JPEG/PNG, max 5MB)
- `GET /api/v1/images/:processingId` - Get processing status and analysis results
