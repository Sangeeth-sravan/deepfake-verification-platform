import React, { useState } from 'react';
import { Upload, FileText, Camera, UserCheck, Sparkles, AlertCircle, ShieldCheck } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import ResultCard from '../components/ResultCard';
import apiService from '../services/api';

export const IdentityVerificationPage = () => {
  const [idFile, setIdFile] = useState(null);
  const [idPreview, setIdPreview] = useState(null);

  const [selfieFile, setSelfieFile] = useState(null);
  const [selfiePreview, setSelfiePreview] = useState(null);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleIdSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('ID Document must be an image file (JPG, PNG).');
        return;
      }
      setError(null);
      setIdFile(file);
      setIdPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleSelfieSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Selfie must be an image file (JPG, PNG).');
        return;
      }
      setError(null);
      setSelfieFile(file);
      setSelfiePreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleVerify = async () => {
    if (!idFile || !selfieFile) {
      setError('Please upload both the ID Document and Selfie photo.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('id_document', idFile);
    formData.append('selfie', selfieFile);

    try {
      const response = await apiService.verifyIdentity(formData);
      setResult(response);
    } catch (err) {
      setError(
        err?.message ||
        'Identity verification failed. Please check that the backend server is running and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Digital Identity <span className="gradient-text">Verification</span></h1>
        <p className="subtext">Extract text via OCR, compare biometric facial embeddings, and check passive anti-spoofing liveness.</p>
      </div>

      {error && (
        <div className="alert-box warning">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <div className="grid-2">
        {/* ID Document Card */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <FileText color="#818cf8" size={20} />
            <h3>1. Upload ID Document</h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '1.25rem' }}>
            Passport, National ID, or Driver's License
          </p>

          <label className="dropzone">
            <input type="file" accept="image/*" onChange={handleIdSelect} style={{ display: 'none' }} />
            <Upload className="dropzone-icon" />
            <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Select ID Document Image</p>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>
              {idFile ? idFile.name : 'JPG, PNG up to 10MB'}
            </span>
          </label>

          {idPreview && (
            <div style={{ marginTop: '1rem', textAlign: 'center' }}>
              <img src={idPreview} alt="ID Preview" style={{ maxHeight: '160px', borderRadius: 'var(--radius-sm)' }} />
            </div>
          )}
        </div>

        {/* Selfie Card */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Camera color="#22d3ee" size={20} />
            <h3>2. Upload Live Selfie</h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '1.25rem' }}>
            Clear front-facing portrait photo
          </p>

          <label className="dropzone">
            <input type="file" accept="image/*" onChange={handleSelfieSelect} style={{ display: 'none' }} />
            <Upload className="dropzone-icon" />
            <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Select Selfie Image</p>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>
              {selfieFile ? selfieFile.name : 'JPG, PNG up to 10MB'}
            </span>
          </label>

          {selfiePreview && (
            <div style={{ marginTop: '1rem', textAlign: 'center' }}>
              <img src={selfiePreview} alt="Selfie Preview" style={{ maxHeight: '160px', borderRadius: 'var(--radius-sm)' }} />
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
        <button
          className="btn btn-primary"
          style={{ minWidth: '280px', padding: '0.9rem 2rem' }}
          onClick={handleVerify}
          disabled={!idFile || !selfieFile || loading}
        >
          <UserCheck size={20} /> Perform Full Identity Audit
        </button>
      </div>

      {loading && <LoadingSpinner label="Running ELA tampering check, face detection, liveness test & similarity scoring..." />}

      {!loading && result && (
        <ResultCard result={result} onDownloadReport={(id) => window.open(apiService.getReportPdfUrl(id))} />
      )}
    </div>
  );
};

export default IdentityVerificationPage;
