import React, { useState } from 'react';
import { Upload, Video as VideoIcon, Sparkles, AlertCircle } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import ResultCard from '../components/ResultCard';
import apiService from '../services/api';

export const VideoDetectionPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('video/')) {
        setError('Please select a valid video file (MP4, AVI, MOV, WEBM).');
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
      const response = await apiService.analyzeVideo(formData);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Video analysis failed. Please try another supported video.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Video AI <span className="gradient-text">Detection</span></h1>
        <p className="subtext">Extract sampled frames, track face landmarks, and compute temporal consistency metrics.</p>
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
          <h3>Upload Video File</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
            Supported formats: MP4, AVI, MOV, WEBM (Max size: 50MB)
          </p>

          <label className="dropzone">
            <input type="file" accept="video/*" onChange={handleFileSelect} style={{ display: 'none' }} />
            <Upload className="dropzone-icon" />
            <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Click or Drag & Drop Video Here</p>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>
              {selectedFile ? selectedFile.name : 'Select file from your device'}
            </span>
          </label>

          <button
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '1.5rem' }}
            onClick={handleAnalyze}
            disabled={!selectedFile || loading}
          >
            <Sparkles size={18} /> Sample Frames & Analyze Video
          </button>
        </div>

        {/* Preview Card */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <h3>Video Preview</h3>
          {previewUrl ? (
            <div style={{ marginTop: '1rem', width: '100%', maxHeight: '280px', display: 'flex', justifyContent: 'center' }}>
              <video
                src={previewUrl}
                controls
                style={{ maxHeight: '260px', maxWidth: '100%', borderRadius: 'var(--radius-sm)' }}
              />
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-subtle)', padding: '3rem 1rem' }}>
              <VideoIcon size={48} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
              <p style={{ fontSize: '0.9rem' }}>No video loaded for analysis</p>
            </div>
          )}
        </div>
      </div>

      {loading && <LoadingSpinner label="Extracting Video Frames & Evaluating Temporal Landmark Consistency..." />}

      {!loading && result && (
        <ResultCard result={result} onDownloadReport={(id) => window.open(apiService.getReportPdfUrl(id))} />
      )}
    </div>
  );
};

export default VideoDetectionPage;
