import React, { useState, useEffect, useCallback } from 'react';
import UploadZone from './components/UploadZone';
import ProcessingView from './components/ProcessingView';
import ResultsView from './components/ResultsView';
import { AlertCircle, RefreshCw } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:3000' : '');

export default function App() {
  const [stage, setStage] = useState('idle'); // 'idle' | 'processing' | 'completed' | 'error'
  const [processingId, setProcessingId] = useState(null);
  const [resultData, setResultData] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Check URL query parameters on mount (e.g. ?id=... or ?processingId=...)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlId = params.get('id') || params.get('processingId');
    if (urlId) {
      console.log(`[App] Initializing from URL query parameter processingId: ${urlId}`);
      setProcessingId(urlId);
      setStage('processing');
    }
  }, []);

  const handleAnalyze = async (file) => {
    setStage('uploading');
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch(`${API_URL}/api/v1/images/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.error || `Upload failed with status ${response.status}`);
      }

      const data = await response.json();
      if (!data.processingId) {
        throw new Error('API response did not contain a processingId.');
      }

      console.log(`[App] Image uploaded successfully. processingId: ${data.processingId}`);
      setProcessingId(data.processingId);
      setStage('processing');
    } catch (err) {
      console.error('[App] Upload error:', err);
      setErrorMessage(err.message || 'Failed to upload image. Please try again.');
      setStage('error');
    }
  };

  const handleProcessingComplete = useCallback((data) => {
    console.log(`[App] Processing completed successfully! Transitioning to results view.`, data);
    setResultData(data);
    setStage('completed');
  }, []);

  const handleProcessingError = useCallback((msg) => {
    console.error(`[App] Processing error reported: ${msg}`);
    setErrorMessage(msg);
    setStage('error');
  }, []);

  const handleReset = () => {
    // Clear URL query parameters if present
    if (window.location.search) {
      window.history.pushState({}, '', window.location.pathname);
    }
    setStage('idle');
    setProcessingId(null);
    setResultData(null);
    setErrorMessage(null);
  };

  return (
    <div className="container">
      {/* Dashboard Header */}
      <header className="header">
        <h1>Vehicle Image Analyzer</h1>
        <p>
          Upload a vehicle image to check image resolution, blur, lighting quality, OCR text, number plate format, and duplicate detection.
        </p>
      </header>

      {/* Main Flow Views */}
      {stage === 'idle' && <UploadZone onAnalyze={handleAnalyze} />}

      {stage === 'uploading' && (
        <div className="card processing-card">
          <div className="spinner"></div>
          <div className="processing-title">Uploading image to server...</div>
        </div>
      )}

      {stage === 'processing' && (
        <ProcessingView
          processingId={processingId}
          onComplete={handleProcessingComplete}
          onError={handleProcessingError}
        />
      )}

      {stage === 'completed' && resultData && (
        <ResultsView resultData={resultData} onReset={handleReset} />
      )}

      {stage === 'error' && (
        <div className="card error-card">
          <AlertCircle className="error-icon" />
          <div className="processing-title" style={{ color: 'var(--danger)' }}>
            Image Processing Error
          </div>
          <div style={{ color: 'var(--text-secondary)', margin: '1rem 0 1.75rem 0' }}>
            {errorMessage || 'An unexpected error occurred while processing the image.'}
          </div>
          <button className="btn btn-secondary" onClick={handleReset}>
            <RefreshCw size={18} />
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
