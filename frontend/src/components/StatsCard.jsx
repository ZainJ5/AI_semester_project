import React from 'react';

const StatsCard = ({ title, value, icon: Icon, color = "#3b82f6", subtitle }) => {
  return (
    <div className="stats-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div className="stats-card-header">
        {Icon && <Icon size={24} style={{ color }} />}
        <h3>{title}</h3>
      </div>
      <div className="stats-card-value">{value}</div>
      {subtitle && <div className="stats-card-subtitle">{subtitle}</div>}
    </div>
  );
};

export default StatsCard;
