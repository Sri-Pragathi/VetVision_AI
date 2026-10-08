import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, AlertOctagon } from 'lucide-react';

export const TriageBadge = ({ level = 'LOW', size = 'md' }) => {
  const normLevel = (level || 'LOW').toUpperCase();

  const config = {
    LOW: {
      label: 'Low Risk',
      badgeClass: 'badge-low',
      Icon: CheckCircle2,
    },
    MODERATE: {
      label: 'Moderate Risk',
      badgeClass: 'badge-moderate',
      Icon: AlertCircle,
    },
    HIGH: {
      label: 'High Urgency',
      badgeClass: 'badge-high',
      Icon: AlertTriangle,
    },
    EMERGENCY: {
      label: 'Emergency Triage',
      badgeClass: 'badge-emergency',
      Icon: AlertOctagon,
    },
  }[normLevel] || {
    label: normLevel,
    badgeClass: 'badge-neutral',
    Icon: AlertCircle,
  };

  const iconSizes = { sm: 12, md: 14, lg: 18 };
  const iconSize = iconSizes[size] || 14;

  return (
    <span className={`badge ${config.badgeClass}`} style={size === 'lg' ? { padding: '6px 14px', fontSize: '14px' } : {}}>
      <config.Icon size={iconSize} strokeWidth={2.5} />
      <span>{config.label}</span>
    </span>
  );
};

export default TriageBadge;
