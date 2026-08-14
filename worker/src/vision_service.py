import os
import base64
import requests
import cv2
import numpy as np
from typing import Dict, Any, Optional

GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY", "").strip()

def _detect_text_with_gemini(img_bgr: np.ndarray, key: str) -> Optional[Dict[str, Any]]:
    """
    Calls Google AI Studio Gemini API (Gemini Flash Vision) which is completely free with no billing needed.
    """
    try:
        success, encoded_img = cv2.imencode('.jpg', img_bgr)
        if not success:
            return None

        b64_content = base64.b64encode(encoded_img).decode('utf-8')

        # Supported multimodal vision models
        models = ["gemini-flash-latest", "gemini-3.1-flash-image-preview", "gemini-2.5-flash-lite"]
        response = None
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            prompt = (
                "Read all visible text in this vehicle image accurately. "
                "Find the vehicle license/registration number plate (such as Indian registration format MH 12 NW 8556, TN 05 BT 5754, MH 12 KR 1145). "
                "Return a JSON object with two fields:\n"
                "- 'fullText': all text found in the image\n"
                "- 'plate': the clean license plate alphanumeric string (e.g. 'MH12NW8556', 'TN05BT5754', 'MH12KR1145') or empty string if not found."
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": b64_content
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json"
                }
            }

            try:
                res = requests.post(url, json=payload, timeout=20)
                if res.status_code == 200:
                    response = res
                    break
                else:
                    print(f"[GeminiVision] Model {model} returned status {res.status_code}: {res.text[:100]}", flush=True)
            except Exception as ex:
                print(f"[GeminiVision] Error requesting {model}: {ex}", flush=True)

        if not response or response.status_code != 200:
            return None

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return None

        content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        import json
        parsed = json.loads(content)
        return {
            "fullText": parsed.get("fullText", ""),
            "plate": parsed.get("plate", ""),
            "blocks": [{"text": parsed.get("plate", "")}] if parsed.get("plate") else []
        }
    except Exception as e:
        print(f"[GeminiVision] API call failed: {e}", flush=True)
        return None


def detect_text_with_google_vision(img_bgr: np.ndarray, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Calls Google Cloud Vision API or Gemini Flash API on an image buffer.
    Supports API Key from Google Cloud Console or Google AI Studio.
    """
    key = (api_key or os.getenv("GOOGLE_VISION_API_KEY", "")).strip()
    if not key:
        return None

    # 1. Try Google Cloud Vision REST
    try:
        success, encoded_img = cv2.imencode('.jpg', img_bgr)
        if not success:
            return None

        b64_content = base64.b64encode(encoded_img).decode('utf-8')

        url = f"https://vision.googleapis.com/v1/images:annotate?key={key}"
        payload = {
            "requests": [
                {
                    "image": {
                        "content": b64_content
                    },
                    "features": [
                        {
                            "type": "TEXT_DETECTION",
                            "maxResults": 50
                        }
                    ]
                }
            ]
        }

        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            responses = data.get("responses", [])
            if responses and responses[0]:
                text_annotations = responses[0].get("textAnnotations", [])
                if text_annotations:
                    full_text = text_annotations[0].get("description", "").strip()
                    blocks = []
                    for ann in text_annotations[1:]:
                        desc = ann.get("description", "").strip()
                        poly = ann.get("boundingPoly", {}).get("vertices", [])
                        blocks.append({
                            "text": desc,
                            "vertices": poly
                        })
                    return {
                        "fullText": full_text,
                        "blocks": blocks
                    }
        else:
            print(f"[GoogleVision] Cloud Vision returned status {response.status_code}, trying Gemini Flash...", flush=True)
    except Exception as e:
        print(f"[GoogleVision] Cloud Vision attempt failed: {e}", flush=True)

    # 2. Try Gemini Flash (Google AI Studio Key)
    return _detect_text_with_gemini(img_bgr, key)

