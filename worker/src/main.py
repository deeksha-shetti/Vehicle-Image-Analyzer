import asyncio
import datetime
import os
import sys
import requests
import numpy as np
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
from pymongo import MongoClient
from bullmq import Worker
from image_pipeline import run_image_analysis


# Global MongoDB Client
mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/vehicle_db")
mongo_client = MongoClient(mongo_uri)

def get_db():
    try:
        return mongo_client.get_default_database()
    except Exception:
        return mongo_client["vehicle_db"]

db = get_db()

def update_vehicle_document(processing_id, update_fields):
    # Try 'vehicle_images' collection first
    coll = db["vehicle_images"]
    res = coll.update_one({"processingId": processing_id}, update_fields)
    
    # Fall back to 'vehicleimages' if document was created with Mongoose default naming
    if res.matched_count == 0:
        fallback_coll = db["vehicleimages"]
        res = fallback_coll.update_one({"processingId": processing_id}, update_fields)
    return res

def fetch_existing_phashes(current_processing_id):
    phashes = []
    try:
        for coll_name in ["vehicle_images", "vehicleimages"]:
            cursor = db[coll_name].find(
                {
                    "processingId": {"$ne": current_processing_id},
                    "analysis.duplicate.pHash": {"$exists": True, "$ne": None}
                },
                {"analysis.duplicate.pHash": 1}
            )
            for doc in cursor:
                p_hash = doc.get("analysis", {}).get("duplicate", {}).get("pHash")
                if p_hash:
                    phashes.append(p_hash)
    except Exception as e:
        print(f"[Worker] Warning fetching existing pHashes: {e}", flush=True)
    return phashes

def sanitize_for_mongo(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_mongo(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_mongo(v) for v in obj]
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

async def process_job(job, token):
    processing_id = None
    try:
        job_id = job.id
        processing_id = job.data.get("processingId")
        storage_url = job.data.get("storageUrl", "")

        print(f"[Worker] Received job {job_id}", flush=True)
        print(f"[Worker] Starting analysis for {processing_id}", flush=True)

        # 1. Update MongoDB status to "processing", reset processedAt & errorMessage
        res_proc = update_vehicle_document(processing_id, {
            "$set": {
                "status": "processing",
                "processedAt": None,
                "errorMessage": None
            }
        })
        if res_proc.matched_count == 0:
            print(f"[Worker] Warning: No MongoDB document found for processingId {processing_id}", flush=True)
        else:
            print("[Worker] Status updated to processing", flush=True)

        # 2. Download image
        response = requests.get(storage_url, timeout=15)
        response.raise_for_status()
        image_bytes = response.content

        # 3. Decode with OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("OpenCV failed to decode image buffer")

        # 4. Fetch existing pHashes for duplicate check
        existing_phashes = fetch_existing_phashes(processing_id)

        # 5. Run full image analysis pipeline
        analysis_result = run_image_analysis(img, existing_phashes)
        analysis_result = sanitize_for_mongo(analysis_result)

        # 6. Structured Safe Logging
        width = analysis_result["dimensions"]["width"]
        height = analysis_result["dimensions"]["height"]
        blur_score = analysis_result["blur"]["blurScore"]
        brightness_score = analysis_result["brightness"]["brightnessScore"]
        quality_score = analysis_result["qualityScore"]
        recommendation = analysis_result["recommendation"]

        print(f"[Worker] Dimensions: {width}x{height}", flush=True)
        print(f"[Worker] Blur score: {blur_score} (severity: {analysis_result['blur']['severity']})", flush=True)
        print(f"[Worker] Brightness score: {brightness_score}", flush=True)
        print("[Worker] OCR completed", flush=True)
        print("[Worker] pHash generated", flush=True)
        print("[Worker] Number plate validation completed", flush=True)
        print(f"[Worker] Quality score: {quality_score}", flush=True)
        print(f"[Worker] Recommendation: {recommendation}", flush=True)

        # 7. Update MongoDB with complete analysis payload and status "completed"
        now = datetime.datetime.now(datetime.timezone.utc)
        update_doc = {
            "$set": {
                "status": "completed",
                "processedAt": now,
                "analysis": analysis_result,
                "errorMessage": None
            }
        }
        update_vehicle_document(processing_id, update_doc)
        print("[Worker] Analysis saved to MongoDB", flush=True)
        print(f"[Worker] Status updated to completed for {processing_id}", flush=True)

        return {"status": "completed", "processingId": processing_id}

    except Exception as e:
        err_msg = str(e)
        print(f"[Worker] Error processing job for {processing_id}: {err_msg}", flush=True)
        if processing_id:
            try:
                now = datetime.datetime.now(datetime.timezone.utc)
                update_vehicle_document(
                    processing_id,
                    {
                        "$set": {
                            "status": "failed",
                            "errorMessage": err_msg,
                            "processedAt": now
                        }
                    }
                )
                print("[Worker] Status updated to failed in MongoDB", flush=True)
            except Exception as db_err:
                print(f"[Worker] Failed to update error status in MongoDB: {db_err}", flush=True)
        return {"status": "failed", "error": err_msg}

async def main():
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD", "")
    queue_name = os.getenv("QUEUE_NAME", "image-processing")

    redis_opts = {
        "host": redis_host,
        "port": redis_port,
    }
    if redis_password:
        redis_opts["password"] = redis_password

    print("[Worker] Connected to Redis", flush=True)
    print("[Worker] Waiting for jobs...", flush=True)

    worker = Worker(queue_name, process_job, {"connection": redis_opts})

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("[Worker] Shutting down gracefully...", flush=True)
        mongo_client.close()
        await worker.close()

if __name__ == "__main__":
    asyncio.run(main())
