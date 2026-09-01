import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

export const RiskBadge = ({ level = 'LOW', score = null }) => {
  const normalizedLevel = (level || 'LOW').toUpperCase();

  const getIcon = () => {
    switch (normalizedLevel) {
      case 'HIGH':
        return <ShieldAlert size={16} />;
      case 'MEDIUM':
        return <AlertTriangle size={16} />;
      case 'LOW':
      default:
        return <ShieldCheck size={16} />;
    }
  };

  return (
    <span className={`risk-badge ${normalizedLevel}`}>
      {getIcon()}
      <span>{normalizedLevel} RISK</span>
      {score !== null && <span style={{ opacity: 0.8, fontSize: '0.8em' }}>({score}/100)</span>}
    </span>
  );
};

export default RiskBadge;
