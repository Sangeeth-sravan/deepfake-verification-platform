import React, { useState } from 'react';
import { Upload, Mic, Sparkles, AlertCircle, Music } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import ResultCard from '../components/ResultCard';
import FileUpload from '../components/FileUpload';
import apiService from '../services/api';

export const AudioAnalysisPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!['audio/wav', 'audio/x-wav', 'audio/wave'].includes(file.type) && !file.name.toLowerCase().endsWith('.wav')) {
        setError('Please select an uncompressed PCM WAV audio file.');
        return;
      }
      if (file.size > 20 * 1024 * 1024) { // 20MB
        setError('File size exceeds the 20MB upload limit.');
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
      const response = await apiService.analyzeAudio(formData);
      setResult(response);
    } catch (err) {
      setError(err.message || 'Audio analysis failed. Please select another WAV file.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Audio & Synthetic Media <span className="gradient-text">Analysis</span></h1>
        <p className="subtext">Inspect voice audio clips for spectral anomalies, TTS artifacts, and neural voice synthesis signatures.</p>
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
          <h3>Upload Audio File</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
            Supported format: uncompressed PCM WAV (Max size: 20MB)
          </p>

          <FileUpload
            accept="audio/wav,.wav"
            onFileSelect={handleFileSelect}
            selectedFile={selectedFile}
            title="Click or Drag & Drop Audio File"
            subtitle="Select audio clip from your device"
            icon={Mic}
          />

          <button
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '1.5rem' }}
            onClick={handleAnalyze}
            disabled={!selectedFile || loading}
          >
            <Sparkles size={18} /> Analyze Audio Authenticity
          </button>
        </div>

        {/* Preview Card */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <h3>Audio Playback Preview</h3>
          {previewUrl ? (
            <div style={{ marginTop: '1.5rem', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <Music size={40} color="#818cf8" />
              <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', fontWeight: 600 }}>{selectedFile?.name}</p>
              <audio src={previewUrl} controls style={{ width: '100%', borderRadius: 'var(--radius-sm)' }} />
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-subtle)', padding: '3rem 1rem' }}>
              <Mic size={48} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
              <p style={{ fontSize: '0.9rem' }}>No audio file loaded for analysis</p>
            </div>
          )}
        </div>
      </div>

      {loading && <LoadingSpinner label="Extracting Mel-Spectrogram & Scanning for Voice Synthesis Artifacts..." />}

      {!loading && result && (
        <ResultCard result={result} onDownloadReport={(id) => window.open(apiService.getReportPdfUrl(id))} />
      )}
    </div>
  );
};

export default AudioAnalysisPage;
