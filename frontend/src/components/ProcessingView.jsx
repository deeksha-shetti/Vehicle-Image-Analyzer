import React, { useEffect, useRef } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

export default function ProcessingView({ processingId, onComplete, onError }) {
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onCompleteRef.current = onComplete;
    onErrorRef.current = onError;
  }, [onComplete, onError]);

  useEffect(() => {
    if (!processingId) return;

    let isSubscribed = true;
    let timerId = null;
    const startTime = Date.now();
    const TIMEOUT_MS = 2 * 60 * 1000;

    const pollStatus = async () => {
      if (!isSubscribed) {
        console.log(`[POLL] isSubscribed is false, aborting poll for ${processingId}`);
        return;
      }

      const elapsed = Date.now() - startTime;
      if (elapsed > TIMEOUT_MS) {
        console.log(`[POLL] 2-minute timeout reached for ${processingId}`);
        isSubscribed = false;
        if (timerId) clearTimeout(timerId);
        if (onErrorRef.current) {
          onErrorRef.current('Processing timed out after 2 minutes. Please try again.');
        }
        return;
      }

      console.log(`[POLL] processingId: ${processingId}`);
      try {
        const response = await fetch(`${API_URL}/api/v1/images/${processingId}`);
        if (!response.ok) {
          throw new Error(`Server returned HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log(`[POLL] API response:`, data);
        console.log(`[POLL] status: ${data ? data.status : 'undefined'}`);

        if (!isSubscribed) {
          console.log(`[POLL] isSubscribed is false after fetch for ${processingId}`);
          return;
        }

        if (data && data.status === 'completed') {
          console.log(`[POLL] completed detected: ${processingId}`);
          console.log(`[POLL] stopping polling: ${processingId}`);
          isSubscribed = false;
          if (timerId) clearTimeout(timerId);
          if (onCompleteRef.current) {
            onCompleteRef.current(data);
          }
        } else if (data && data.status === 'failed') {
          console.log(`[POLL] failed detected: ${processingId}`);
          console.log(`[POLL] stopping polling: ${processingId}`);
          isSubscribed = false;
          if (timerId) clearTimeout(timerId);
          if (onErrorRef.current) {
            onErrorRef.current(data.errorMessage || 'Image processing failed on worker.');
          }
        } else if (data && (data.status === 'pending' || data.status === 'processing')) {
          timerId = setTimeout(pollStatus, 1500);
        } else {
          console.log(`[POLL] unknown status fallback: ${data ? data.status : 'null'}`);
          timerId = setTimeout(pollStatus, 1500);
        }
      } catch (err) {
        if (isSubscribed) {
          console.error('[POLL] Polling fetch error:', err);
          timerId = setTimeout(pollStatus, 2000);
        }
      }
    };

    pollStatus();

    return () => {
      console.log(`[POLL] Cleaning up ProcessingView effect for ${processingId}`);
      isSubscribed = false;
      if (timerId) clearTimeout(timerId);
    };
  }, [processingId]);

  return (
    <div className="card processing-card">
      <div className="spinner"></div>
      <div className="processing-title">Processing your image...</div>
      <div className="processing-id">Processing ID: {processingId}</div>
    </div>
  );
}
