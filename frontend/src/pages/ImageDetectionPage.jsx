import React, { useState } from 'react';
import { Image as ImageIcon, Sparkles, AlertCircle } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import ResultCard from '../components/ResultCard';
import FileUpload from '../components/FileUpload';
import apiService from '../services/api';

export const ImageDetectionPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        setError('Please select a valid image file (JPG, PNG, WEBP).');
        return;
      }
      if (file.size > 50 * 1024 * 1024) { // 50MB
        setError('File size exceeds the 50MB upload limit.');
        return;
      }
      setError(null);
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await apiService.analyzeImage(formData);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Image forensic analysis failed. Please try again.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Image AI <span className="gradient-text">Detection</span></h1>
        <p className="subtext">Upload single images for Error Level Analysis (ELA) and Fourier frequency domain inspection.</p>
      </div>

      {error && (
        <div className="alert-box warning">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <div className="grid-2">
        {/* Upload Card */}
        <div className="glass-card">
          <h3>Upload Image File</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
            Supported formats: JPG, PNG, WEBP (Max size: 50MB)
          </p>

          <FileUpload
            accept="image/*"
            onFileSelect={handleFileSelect}
            selectedFile={selectedFile}
            title="Click or Drag & Drop Image Here"
            subtitle="Select file from your device"
            icon={ImageIcon}
          />

          <button
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '1.5rem' }}
            onClick={handleAnalyze}
            disabled={!selectedFile || loading}
          >
            <Sparkles size={18} /> Analyze Image Authenticity
          </button>
        </div>

        {/* Preview Card */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <h3>Image Preview</h3>
          {previewUrl ? (
            <div style={{ marginTop: '1rem', width: '100%', maxHeight: '280px', display: 'flex', justifyContent: 'center' }}>
              <img
                src={previewUrl}
                alt="Upload Preview"
                style={{ maxHeight: '260px', maxWidth: '100%', borderRadius: 'var(--radius-sm)', objectFit: 'contain' }}
              />
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-subtle)', padding: '3rem 1rem' }}>
              <ImageIcon size={48} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
              <p style={{ fontSize: '0.9rem' }}>No image loaded for analysis</p>
            </div>
          )}
        </div>
      </div>

      {loading && <LoadingSpinner label="Executing Error Level Analysis (ELA) & 2D Fourier Spectrum Forensics..." />}

      {!loading && result && (
        <ResultCard result={result} onDownloadReport={(id) => window.open(apiService.getReportPdfUrl(id))} />
      )}
    </div>
  );
};

export default ImageDetectionPage;
