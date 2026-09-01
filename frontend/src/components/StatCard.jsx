import React from 'react';

export const StatCard = ({ title, value, icon: Icon, color = '#818cf8', subtitle }) => {
  return (
    <div className="glass-card">
      <span style={{ fontSize: '0.85rem', color: 'var(--text-subtle)', fontWeight: 600, textTransform: 'uppercase' }}>
        {title}
      </span>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem' }}>
        <span style={{ fontSize: '2rem', fontWeight: 800, color: color }}>{value}</span>
        {Icon && <Icon size={28} color={color} />}
      </div>
      {subtitle && (
        <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', marginTop: '0.25rem', display: 'block' }}>
          {subtitle}
        </span>
      )}
    </div>
  );
};

export default StatCard;
