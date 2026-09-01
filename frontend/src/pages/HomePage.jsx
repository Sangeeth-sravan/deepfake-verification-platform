import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Image, Video, UserCheck, Cpu, Lock, ArrowRight, Activity, FileCheck } from 'lucide-react';

export const HomePage = () => {
  return (
    <div>
      {/* Hero Section */}
      <section style={{ textAlign: 'center', padding: '3.5rem 1rem 2.5rem 1rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.3)', padding: '0.4rem 1rem', borderRadius: '30px', color: '#a5b4fc', fontSize: '0.85rem', fontWeight: 600, marginBottom: '1.5rem' }}>
          <Cpu size={16} /> AI-POWERED MEDIA FORENSICS & IDENTITY AUTHENTICATION
        </div>

        <h1 style={{ fontSize: '3rem', fontWeight: 800, maxW: '900px', margin: '0 auto 1.25rem' }}>
          Detect Deepfakes, Synthetic Media & <span className="gradient-text">Verify Digital Identity</span>
        </h1>

        <p className="subtext" style={{ maxWidth: '720px', margin: '0 auto 2.5rem', fontSize: '1.1rem' }}>
          A multi-layered forensic platform that analyzes image artifacts, video frame consistency, and performs biometric identity verification with passive liveness detection.
        </p>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/image-detection" className="btn btn-primary">
            Analyze Media <ArrowRight size={18} />
          </Link>
          <Link to="/identity-verification" className="btn btn-secondary">
            Verify Digital Identity <UserCheck size={18} />
          </Link>
        </div>
      </section>

      {/* Feature Grid */}
      <section style={{ marginTop: '3rem' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>Platform Core Features</h2>

        <div className="grid-3">
          <div className="glass-card glass-card-interactive">
            <div style={{ background: 'rgba(99, 102, 241, 0.15)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <Image size={24} color="#818cf8" />
            </div>
            <h3>Image Forensic Analysis</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Evaluates Error Level Analysis (ELA), Fourier frequency anomalies, and GAN compression artifacts to detect image manipulation.
            </p>
          </div>

          <div className="glass-card glass-card-interactive">
            <div style={{ background: 'rgba(6, 182, 212, 0.15)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <Video size={24} color="#22d3ee" />
            </div>
            <h3>Video Deepfake Analysis</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Performs intelligent frame sampling, face trajectory tracking, and temporal consistency scoring across video sequences.
            </p>
          </div>

          <div className="glass-card glass-card-interactive">
            <div style={{ background: 'rgba(217, 70, 239, 0.15)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <UserCheck size={24} color="#e879f9" />
            </div>
            <h3>Digital Identity Verification</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Extracts text from government IDs via OCR, compares biometric facial embeddings, and runs passive anti-spoofing liveness checks.
            </p>
          </div>
        </div>
      </section>

      {/* Modular Risk Engine & Compliance Banner */}
      <section className="glass-card" style={{ marginTop: '3.5rem', background: 'linear-gradient(135deg, rgba(18, 24, 36, 0.9) 0%, rgba(30, 41, 64, 0.6) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '280px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#818cf8', fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.5rem' }}>
              <Activity size={18} /> MULTI-SIGNAL RISK ENGINE
            </div>
            <h2 style={{ fontSize: '1.75rem', marginBottom: '0.75rem' }}>Automated Risk Scoring (0–100)</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              Combines deepfake probabilities, face feature vector distances, OCR text cross-checks, and passive liveness metrics into a unified security score.
            </p>
          </div>
          <div>
            <Link to="/dashboard" className="btn btn-primary">
              View Analytics Dashboard
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
