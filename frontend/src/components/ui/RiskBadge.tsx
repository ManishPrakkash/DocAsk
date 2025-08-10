import React from 'react';
import { RiskLevel } from '../../types';

interface RiskBadgeProps {
  riskLevel: RiskLevel;
  riskScore: number;
  size?: 'sm' | 'md' | 'lg';
}

const RiskBadge: React.FC<RiskBadgeProps> = ({ riskLevel, riskScore, size = 'md' }) => {
  const colorClasses = {
    [RiskLevel.LOW]: 'bg-green-100 text-green-800 border-green-200',
    [RiskLevel.MEDIUM]: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    [RiskLevel.HIGH]: 'bg-orange-100 text-orange-800 border-orange-200',
    [RiskLevel.CRITICAL]: 'bg-red-100 text-red-800 border-red-200',
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-2.5 py-1.5 text-sm',
    lg: 'px-3 py-2 text-base',
  };

  return (
    <div
      className={`
        inline-flex items-center gap-1 rounded-full border 
        ${colorClasses[riskLevel]} ${sizeClasses[size]}
        font-medium
      `}
    >
      <span>{riskLevel.toUpperCase()}</span>
      <span className="text-gray-500 text-xs ml-1">
        ({Math.round(riskScore * 100)}%)
      </span>
    </div>
  );
};

export default RiskBadge;
