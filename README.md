# Vehicle-Image-Analyzer
Vehicle Image Analysis & Validation System

Engineering Documentation / README

1. Overview

The Vehicle Image Analysis & Validation System is a production-oriented image processing system for analyzing vehicle images and determining whether they are suitable for downstream use.

It evaluates image quality, extracts OCR text, detects and validates Indian vehicle number plates, identifies duplicate images, checks for possible screenshots and tampering, and produces an overall quality score and recommendation.

The application uses an asynchronous architecture so computationally expensive image processing does not block the API request.

2. Key Features

Image quality analysis: dimensions, blur/sharpness, brightness and quality scoring.

General OCR and number-plate analysis, including localization, preprocessing, perspective correction, Indian registration validation and OCR confidence scoring.

Perceptual hashing and duplicate detection, screenshot detection and basic tampering/suspicion detection.

REST API, asynchronous processing, Redis + BullMQ, Python worker, MongoDB and Cloudinary.

Frontend upload, processing status and analysis visualization.

Docker Compose, modular services, processing IDs, logging and error handling.

3. Architecture

Frontend (React)
        |
        v
Node.js API (Express)
   |             |
   |             +----> MongoDB
   +----> Cloudinary
   +----> Redis + BullMQ
              |
              v
        Python Worker
        | OpenCV
        | Tesseract OCR
        | Image Heuristics
        v
        MongoDB

4. Service Flow

Frontend selects and uploads a vehicle image.

Node.js API validates the file and generates a processing ID.

The image is uploaded to Cloudinary and metadata is stored in MongoDB.

A BullMQ job is placed in Redis.

The API immediately returns the processing ID and pending status.

The Python worker consumes the job and performs image analysis.

The worker stores the analysis and final status in MongoDB.

The frontend retrieves the result through the processing ID.

5. Processing Flow

Image Upload
     |
File Validation
     |
Cloudinary Upload
     |
MongoDB Record
     |
BullMQ Job
     |
Python Worker
     |
     +--> Dimensions
     +--> Blur
     +--> Brightness
     +--> Screenshot Detection
     +--> Tampering Detection
     +--> pHash / Duplicate Detection
     +--> General OCR
     +--> Number Plate Detection + OCR
     |
Quality Score + Recommendation
     |
MongoDB
     |
API Result

6. Queue Strategy

Image processing is asynchronous because OCR and computer-vision operations can be computationally expensive. The API does not wait for the complete analysis before responding.

The client receives a processingId and can use it to retrieve the current status. This keeps API response times short and allows additional workers to consume jobs from the same queue as traffic increases.

Client -> API -> Redis/BullMQ -> Worker -> MongoDB
             |
             +---- immediate response with processingId

7. Major Design Decisions

Separate the API from image processing so HTTP handling is not coupled to expensive OCR/CV work.

Use BullMQ/Redis for asynchronous processing and future worker scaling.

Use Cloudinary for image binaries and MongoDB for metadata and analysis.

Combine multiple independent signals instead of relying on one heuristic.

Keep general OCR separate from number-plate OCR to reduce advertisement-text false positives.

Prefer explainable heuristics where practical to keep the current solution lightweight and debuggable.

8. Analysis Pipeline

8.1 Image Dimensions

The worker extracts image width and height and uses the result as one signal of whether the image has sufficient resolution for analysis.

8.2 Blur Detection

Blur is estimated using variance of the Laplacian. Sharp images generally produce stronger edges and higher variance, while blurred images tend to produce lower variance. The result is converted into a severity level. This is a heuristic rather than a universal definition of image quality.

8.3 Brightness Analysis

The image is converted to grayscale and average brightness is calculated to identify significantly dark or underexposed images.

8.4 Duplicate Detection

A perceptual hash (pHash) is generated for each image. Unlike a normal file hash, a perceptual hash represents visual characteristics and can identify visually similar images even when their binary files differ.

8.5 Screenshot Detection

Image-level heuristics identify characteristics associated with screenshots. The result is treated as a probabilistic suspicion signal.

8.6 Tampering Detection

Lightweight image-forensics heuristics identify suspicious characteristics. This is treated as a suspicion signal rather than proof of manipulation.

9. Number Plate Detection

Number plate detection is treated separately from general OCR. Vehicle images can contain large amounts of advertisement and environmental text. General OCR may correctly recognize that text, but it should not automatically be interpreted as a vehicle registration number.

General OCR -> General scene text

Plate Detection -> Candidate -> Preprocessing / Perspective Correction
                 -> Plate OCR -> Indian Registration Validation -> Confidence

9.1 Plate Detection Pipeline

Vehicle-region filtering

Yellow-region detection

Candidate generation

Candidate filtering

Perspective correction

Crop preprocessing

OCR

OCR normalization

Indian registration validation

Confidence scoring

9.2 Indian Number Plate Validation

OCR output is normalized before validation. For example, 'TN 05 BT 5754' can be normalized to 'TN05BT5754'. The validation stage checks the expected structure of an Indian registration number and uses state/UT prefixes to reduce false positives.

OCR can confuse visually similar characters. Normalization may account for common confusions such as O/0, I/1, L/1, S/5 and B/8, but the final candidate must still satisfy registration validation rules.

10. Quality Scoring

The system combines multiple signals into an overall quality score. The score is intended as a practical decision signal rather than a universal image-quality measurement.

ACCEPT — image is sufficiently clear and no significant issues were detected.

REVIEW — image may still be usable but one or more concerns were detected.

REJECT — significant issues make the image unsuitable for downstream use.

11. API Design

11.1 Upload Image

POST /api/v1/images/upload

curl.exe -X POST "http://localhost:3000/api/v1/images/upload" -F "image=@C:\path\to\image.png"

{"message":"Image uploaded and queued for processing.","processingId":"example-processing-id","status":"pending"}

11.2 Retrieve Analysis

GET /api/v1/images/:processingId

curl.exe "http://localhost:3000/api/v1/images/example-processing-id"

12. Processing States

pending
   |
   v
processing
   |
   +----> completed
   |
   +----> failed

pending — image uploaded and processing job queued.

processing — worker has picked up the job.

completed — analysis finished successfully.

failed — unexpected processing error occurred.

13. Data Model

VehicleImage
|-- processingId
|-- originalFilename
|-- storageUrl
|-- status
|-- uploadedAt
|-- processedAt
|-- analysis
|   |-- recommendation
|   |-- dimensions
|   |-- blur
|   |-- brightness
|   |-- duplicate
|   |-- screenshotDetection
|   |-- tampering
|   |-- ocr
|   |-- numberPlate
|   |-- qualityScore
|   +-- issues
+-- errorMessage

14. Running Locally

Prerequisites: Git and Docker Desktop. Docker is recommended because the project depends on MongoDB, Redis, Node.js and the Python OCR worker.

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Gogig-Assignment
docker compose up -d
docker compose ps

Expected services are API, frontend, worker, MongoDB and Redis.

15. Docker Setup

Docker Compose provides a reproducible development environment. The worker container contains dependencies required for Python, OpenCV, Tesseract OCR, NumPy and image processing, avoiding manual OCR environment configuration.

16. Testing

docker compose exec worker pytest
docker compose exec worker pytest tests/

Deterministic components can be tested through automated tests. Real-world computer-vision behavior is additionally evaluated using representative vehicle images because image-processing accuracy cannot be completely established through unit tests alone.

17. Failure Handling

When processing starts, the worker records status=processing. On success it records status=completed and processedAt. On an exception it records status=failed, errorMessage and processedAt.

This prevents jobs from remaining indefinitely in the processing state and makes failures visible through the API.

18. Logging and Debugging

[Worker] Received job <jobId>
[Worker] Starting analysis for <processingId>
[Worker] Status updated to processing
[Plate] Vehicle-region candidates: N
[Plate] Plate OCR: '...'
[Worker] Dimensions: ...
[Worker] Blur score: ...
[Worker] Brightness score: ...
[Worker] OCR completed
[Worker] pHash generated
[Worker] Number plate validation completed
[Worker] Quality score: ...
[Worker] Recommendation: ...
[Worker] Analysis saved to MongoDB
[Worker] Status updated to completed

Detailed logs make it possible to identify whether a failure occurs during candidate detection, crop extraction, preprocessing, OCR or validation rather than treating the pipeline as a black box.

19. Trade-offs

19.1 What Was Intentionally Simplified

Variance of Laplacian was used for blur detection instead of a trained image-quality model.

Screenshot detection uses lightweight heuristics instead of a dedicated classifier.

Tampering detection is lightweight and should not be interpreted as forensic proof.

Number plate detection currently uses OpenCV-based localization and OCR rather than a dedicated object-detection model.

These choices reduce infrastructure complexity and make the current system easier to run, explain and debug. The trade-off is reduced robustness on difficult images such as very small, occluded, severely angled or poorly illuminated plates.

20. Scalability Considerations

                    Redis
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Worker 1    Worker 2    Worker 3
          |           |           |
          +-----------+-----------+
                      |
                      v
                   MongoDB

Tesseract can become CPU-intensive at higher volumes, so worker concurrency and autoscaling should be controlled.

MongoDB would require appropriate indexes, pagination and retention policies as analysis history grows.

Redis queue depth and memory should be monitored.

Cloudinary bandwidth/storage costs increase with usage, so compression and retention policies may become important.

21. AI Usage Disclosure

AI was used as a development assistant throughout the project. It helped with understanding requirements, brainstorming architecture, generating implementation approaches, debugging errors, suggesting OpenCV and OCR techniques, reviewing code structure, suggesting tests, improving documentation and interpreting logs.

AI was not treated as the final authority for correctness. Important changes were tested against the actual application.

21.1 Where AI Output Was Wrong

The number-plate pipeline demonstrated that AI-generated code can appear logically correct while failing on real-world images.

Some early approaches detected advertisement regions instead of plates.

Words such as 'ANIMATION' could be incorrectly treated as possible plate text.

Loose OCR matching could produce false-positive registration numbers.

Valid plates could be missed because of overly strict localization or confidence thresholds.

Broad OCR fallbacks could increase noise and processing time.

The resulting engineering distinction was: successful OCR execution is not the same as correct plate detection, and a string matching a loose pattern is not necessarily the correct registration number.

21.2 How AI-Generated Code Was Validated

Test with real vehicle images across front/rear views, yellow plates, tilted plates, small plates, different lighting and advertisement-heavy scenes.

Inspect worker logs using docker compose logs worker.

Verify API results directly using the processingId endpoint.

Verify Docker service health with docker compose ps.

Inspect intermediate candidate regions when the final plate result is incorrect.

Distinguish detection failure, OCR failure and validation failure before changing the implementation.

22. AI-Assisted Development Workflow

Identify problem
      |
Ask AI for possible approaches
      |
Implement
      |
Run actual application
      |
Inspect logs / API output
      |
Compare expected vs actual
      |
Identify failure
      |
Modify
      |
Retest

The main lesson was that AI can accelerate implementation, but real inputs, tests, logs and measurable results determine whether the implementation is actually correct.

23. Future Improvements

Use a dedicated number-plate object-detection model before OCR.

Use specialized plate OCR optimized for perspective, blur and low-resolution images.

Introduce stronger trained image-forensics models.

Build a labelled benchmark dataset and track plate precision, recall, character accuracy, full-plate accuracy, false-positive rate and latency.

Autoscale workers based on queue depth.

Add structured logs, metrics, queue-depth monitoring and distributed job/request IDs.

Add rate limiting to public upload endpoints.

24. Assumptions

Uploaded images are JPEG or PNG files.

The primary target is vehicle imagery.

Indian vehicle registration plates are the primary number-plate format.

OCR is probabilistic and can contain character-level errors.

Image-quality scores are heuristic indicators rather than universal standards.

Screenshot and tampering detection are probabilistic signals.

REVIEW indicates that the image may still be usable but requires attention.

Image processing is asynchronous because OCR and computer vision can be computationally expensive.

Cloudinary stores images while MongoDB stores metadata and analysis.

25. Evaluation Criteria Alignment

Evaluation Area

How the Project Addresses It

Engineering Quality

Modular Node.js API and Python worker

Code Structure

Separate services and focused analysis functions

Readability

Explicit processing stages and logging

Maintainability

Independent image-analysis components

API Design

REST API with processing IDs

Problem Solving

Multiple heuristics instead of one signal

Ambiguity Handling

Confidence scores and REVIEW recommendation

System Thinking

Redis/BullMQ asynchronous architecture

Failure Handling

Explicit pending, processing, completed and failed states

Scalability

Worker-based architecture

Data Modeling

MongoDB analysis document

Debugging

Detailed worker logs and intermediate candidate inspection

Reliability

Automated tests and real-image validation

AI Usage

AI-assisted development with actual validation

Confidence Scoring

OCR and detection confidence values

Docker

Docker Compose setup

Observability

Worker and API logging

26. Engineering Philosophy

The central design philosophy is: keep the API responsive, move expensive processing to a background worker, make analysis signals explainable, and make failures observable.

The project intentionally avoids overengineering where a simpler approach is sufficient, while leaving room for future improvements such as dedicated number-plate detection models, specialized OCR, worker autoscaling, stronger image forensics and production-grade observability.

The focus is not on using the largest number of technologies, but on building a system that is practical, understandable, testable and debuggable.

27. Final Submission Checklist

Git repository is up to date.

README.md is included.

Docker Compose starts successfully.

API starts successfully.

Worker connects to Redis.

MongoDB connects successfully.

Frontend starts successfully.

Image upload works.

Processing ID is returned.

Worker receives the job.

Analysis is saved to MongoDB.

GET /api/v1/images/:processingId works.

Failed jobs are handled correctly.

Tests pass.

Sample API request and response are included.

AI usage disclosure is included.

Assumptions are documented.

Final number-plate implementation is tested on representative images.
