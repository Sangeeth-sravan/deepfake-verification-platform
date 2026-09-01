import React from 'react';

export const ConfidenceBar = ({ label = 'Confidence Score', value = 0, color = '#818cf8' }) => {
  const percentage = Math.min(100, Math.max(0, (value || 0) * 100));

  return (
    <div style={{ margin: '0.75rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
        <span style={{ color: 'var(--text-muted)' }}>{label}</span>
        <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{percentage.toFixed(1)}%</span>
      </div>
      <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '4px', overflow: 'hidden' }}>
        <div
          style={{
            width: `${percentage}%`,
            height: '100%',
            background: color,
            borderRadius: '4px',
            transition: 'width 0.5s ease-in-out',
          }}
        />
      </div>
    </div>
  );
};

export default ConfidenceBar;
