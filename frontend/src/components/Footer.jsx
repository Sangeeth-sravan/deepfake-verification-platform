import React from 'react';
import { AlertCircle, Code2 } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <p style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', justifyContent: 'center' }}>
          <Code2 size={16} className="text-indigo-400" />
          <span>Real-Time AI-Powered Deepfake, Synthetic Media & Digital Identity Verification Platform</span>
        </p>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', maxWidth: '800px', margin: '0 auto' }}>
          <AlertCircle size={14} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
          <strong>Academic Prototype Disclaimer:</strong> Accuracy depends on sample quality, media format, and trained baseline algorithms. Evaluated for academic demonstration.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
