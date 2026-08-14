import React, { useState, useRef } from 'react';
import { Upload, Image as ImageIcon, AlertCircle } from 'lucide-react';

export default function UploadZone({ onAnalyze }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const validateAndSetFile = (file) => {
    setError(null);

    if (!file) return;

    // Validate type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!validTypes.includes(file.type)) {
      setError('Invalid file format. Please upload a JPEG or PNG image.');
      setSelectedFile(null);
      setPreviewUrl(null);
      return;
    }

    // Validate size (5MB limit)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File size exceeds 5MB. Please choose a smaller image.');
      setSelectedFile(null);
      setPreviewUrl(null);
      return;
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyzeClick = () => {
    if (selectedFile && onAnalyze) {
      onAnalyze(selectedFile, previewUrl);
    }
  };

  return (
    <div className="card">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/jpeg,image/png,image/jpg"
        style={{ display: 'none' }}
      />

      <div
        className={`dropzone ${isDragging ? 'active' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="dropzone-icon" />
        <div className="dropzone-title">
          {selectedFile ? selectedFile.name : 'Drag & drop your vehicle image here'}
        </div>
        <div className="dropzone-desc">
          Supports JPG, JPEG, and PNG files up to 5MB
        </div>
      </div>

      {error && (
        <div style={{ color: 'var(--danger)', marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {previewUrl && (
        <div className="preview-container">
          <div className="preview-img-wrapper">
            <img src={previewUrl} alt="Selected Vehicle Preview" />
          </div>
          <button className="btn btn-primary" onClick={handleAnalyzeClick}>
            <ImageIcon size={18} />
            Analyze Image
          </button>
        </div>
      )}
    </div>
  );
}
