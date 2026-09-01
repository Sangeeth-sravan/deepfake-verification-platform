import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Download, Activity, ShieldCheck } from 'lucide-react';
import RiskBadge from './RiskBadge';
import ConfidenceBar from './ConfidenceBar';

/**
 * ResultCard renders a forensic verification result for any of the four
 * verification types: IMAGE, VIDEO, AUDIO, DIGITAL_IDENTITY.
 *
 * Props:
 *   result          – the API response object
 *   onDownloadReport – callback(verification_id) triggered by the PDF button
 */
export const ResultCard = ({ result, onDownloadReport }) => {
  if (!result) return null;

  const vtype = result.verification_type || '';
  const isReal = ['REAL', 'VERIFIED', 'LIKELY_AUTHENTIC'].includes(result.result);
  const isWarning = ['REQUIRES_REVIEW', 'SUSPICIOUS'].includes(result.result);
  const forensics = result.forensics;

  const isAudio    = vtype === 'AUDIO';
  const isIdentity = vtype === 'DIGITAL_IDENTITY';
  const isImage    = vtype === 'IMAGE';
  // VIDEO falls through to the image branch (shares image forensic field names)

  /* ---- Status icon ---- */
  const StatusIcon = isReal
    ? () => <CheckCircle2 size={32} color="#10b981" />
    : isWarning
      ? () => <AlertTriangle size={32} color="#f59e0b" />
      : () => <XCircle size={32} color="#ef4444" />;

  return (
    <div className="glass-card" style={{ marginTop: '2rem' }}>

      {/* ── Header row ── */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
        flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem',
        paddingBottom: '1rem', borderBottom: '1px solid var(--glass-border)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <StatusIcon />
          <div>
            <h2 style={{ fontSize: '1.5rem', margin: 0 }}>{result.result || 'ANALYZED'}</h2>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-subtle)' }}>
              Type: {vtype || 'Media Scan'}
              {result.filename ? ` • File: ${result.filename}` : ''}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <RiskBadge level={result.risk_level} score={result.risk_score} />
          {result.verification_id && onDownloadReport && (
            <button
              className="btn btn-secondary"
              onClick={() => onDownloadReport(result.verification_id)}
            >
              <Download size={16} /> Download Report
            </button>
          )}
        </div>
      </div>

      {/* ── Primary metric row ── */}
      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', textTransform: 'uppercase' }}>Confidence Score</span>
          <p style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '0.2rem' }}>
            {result.confidence != null ? `${(result.confidence * 100).toFixed(1)}%` : 'N/A'}
          </p>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', textTransform: 'uppercase' }}>Overall Risk</span>
          <p style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '0.2rem' }}>
            {result.risk_score != null ? `${result.risk_score} / 100` : 'N/A'}
          </p>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: 'var(--radius-sm)' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', textTransform: 'uppercase' }}>Verification ID</span>
          <p style={{ fontSize: '1rem', fontWeight: 600, color: '#818cf8', marginTop: '0.4rem', wordBreak: 'break-all' }}>
            {result.verification_id || 'N/A'}
          </p>
        </div>
      </div>

      {/* ── Forensic signal breakdown ── */}
      {forensics && (
        <div style={{
          background: 'rgba(255,255,255,0.02)', padding: '1.25rem',
          borderRadius: 'var(--radius-sm)', marginBottom: '1.5rem',
          border: '1px solid var(--glass-border)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: '#818cf8', fontWeight: 600, fontSize: '0.9rem' }}>
            <Activity size={16} /> FORENSIC SIGNAL METRICS
          </div>

          {/* ---- AUDIO branch ---- */}
          {isAudio && (
            <div className="grid-2">
              <ConfidenceBar
                label="Spectral Anomaly"
                value={forensics.spectral_anomaly_score}
                color={forensics.spectral_anomaly_score > 0.5 ? '#f59e0b' : '#10b981'}
              />
              <ConfidenceBar
                label="Waveform Anomaly"
                value={forensics.waveform_anomaly_score}
                color={forensics.waveform_anomaly_score > 0.5 ? '#ef4444' : '#10b981'}
              />
              <ConfidenceBar
                label="Amplitude Consistency Anomaly"
                value={forensics.consistency_anomaly_score}
                color={forensics.consistency_anomaly_score > 0.5 ? '#f59e0b' : '#10b981'}
              />
              <div style={{ margin: '0.75rem 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                {forensics.duration_seconds}s &nbsp;•&nbsp; {forensics.sample_rate_hz} Hz
                &nbsp;•&nbsp; {forensics.channels} ch &nbsp;•&nbsp; {forensics.sample_width_bits}-bit PCM
              </div>
            </div>
          )}

          {/* ---- DIGITAL_IDENTITY branch ---- */}
          {isIdentity && (
            <div className="grid-2">
              <ConfidenceBar
                label="ID Document ELA (Tampering Risk)"
                value={forensics.id_ela_score}
                color={forensics.id_ela_score > 0.5 ? '#ef4444' : '#10b981'}
              />
              <ConfidenceBar
                label="Edge Integrity (Compositing Risk)"
                value={forensics.id_edge_risk_score}
                color={forensics.id_edge_risk_score > 0.5 ? '#f59e0b' : '#10b981'}
              />
              <ConfidenceBar
                label="Face Similarity (ID vs Selfie)"
                value={Math.min(1, forensics.face_similarity_score * 5)}
                color="#818cf8"
              />
              {/* Liveness indicator */}
              <div style={{ margin: '0.75rem 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Passive Liveness Check</span>
                  <span style={{ fontWeight: 700, color: forensics.selfie_liveness_passed ? '#10b981' : '#ef4444' }}>
                    {forensics.selfie_liveness_passed ? 'PASSED' : 'FAILED'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', color: 'var(--text-subtle)' }}>
                  <span>ID Document faces detected: {forensics.id_face_count}</span>
                  <span>Selfie faces detected: {forensics.selfie_face_count}</span>
                </div>
              </div>
              <div style={{ margin: '0.75rem 0', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                ID: {forensics.id_width}×{forensics.id_height}px &nbsp;•&nbsp;
                Selfie: {forensics.selfie_width}×{forensics.selfie_height}px &nbsp;•&nbsp;
                Liveness texture var: {forensics.selfie_liveness_texture_var}
              </div>
            </div>
          )}

          {/* ---- IMAGE / VIDEO branch ---- */}
          {!isAudio && !isIdentity && (
            <div className="grid-2">
              <ConfidenceBar
                label="Error Level Analysis (ELA) Compression Anomaly"
                value={forensics.ela_score}
                color={forensics.ela_score > 0.5 ? '#ef4444' : '#10b981'}
              />
              <ConfidenceBar
                label="Fourier Frequency Spectrum Anomaly"
                value={forensics.frequency_score}
                color={forensics.frequency_score > 0.5 ? '#f59e0b' : '#10b981'}
              />
              <ConfidenceBar
                label="Sensor Noise Variance Anomaly"
                value={forensics.noise_score}
                color={forensics.noise_score > 0.5 ? '#f59e0b' : '#10b981'}
              />
              <div style={{ margin: '0.75rem 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>
                    {vtype === 'VIDEO' ? 'Avg Frame Sharpness' : 'Image Sharpness'} (Laplacian Var)
                  </span>
                  <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                    {forensics.sharpness_score != null ? forensics.sharpness_score : '—'}
                  </span>
                </div>
                <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${Math.min(100, ((forensics.sharpness_score || 0) / 500) * 100)}%`,
                    height: '100%', background: '#818cf8', borderRadius: '4px'
                  }} />
                </div>
                {vtype === 'VIDEO' && forensics.sampled_frames != null && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.82rem', color: 'var(--text-subtle)' }}>
                    Analysed {forensics.sampled_frames} sampled frames
                    {forensics.fps != null ? ` • ${forensics.fps.toFixed(1)} fps` : ''}
                    {forensics.width != null ? ` • ${forensics.width}×${forensics.height}` : ''}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Detected forensic issues ── */}
      {result.detected_issues && result.detected_issues.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: 'var(--text-muted)' }}>
            Detected Signals &amp; Observations:
          </h4>
          <ul style={{ listStyleType: 'disc', paddingLeft: '1.25rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {result.detected_issues.map((issue, idx) => (
              <li key={idx} style={{ marginBottom: '0.35rem' }}>{issue}</li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Explanation ── */}
      {result.explanation && (
        <p style={{
          marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)',
          fontStyle: 'italic', background: 'rgba(255,255,255,0.02)',
          padding: '0.75rem', borderRadius: 'var(--radius-sm)'
        }}>
          {result.explanation}
        </p>
      )}

      {/* ── Timestamp (shown when loaded from history details) ── */}
      {result.timestamp && (
        <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-subtle)', textAlign: 'right' }}>
          Recorded: {new Date(result.timestamp).toLocaleString()}
        </p>
      )}
    </div>
  );
};

export default ResultCard;
