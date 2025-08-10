import React from 'react';
import { Clause } from '../../types';
import RiskBadge from '../ui/RiskBadge';

interface ClauseHighlightProps {
  clause: Clause;
  isSelected: boolean;
  onClick: () => void;
}

const ClauseHighlight: React.FC<ClauseHighlightProps> = ({
  clause,
  isSelected,
  onClick,
}) => {
  return (
    <div
      className={`
        p-4 rounded-lg mb-4 cursor-pointer transition-all
        ${
          isSelected
            ? 'bg-indigo-50 border-2 border-indigo-500'
            : 'bg-white border border-gray-200 hover:border-indigo-300'
        }
      `}
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-2">
        <div className="text-sm font-medium text-gray-600">
          {clause.category}
          {clause.subcategory && (
            <span className="text-gray-400"> / {clause.subcategory}</span>
          )}
        </div>
        <RiskBadge
          riskLevel={clause.risk_level}
          riskScore={clause.risk_score}
          size="sm"
        />
      </div>
      
      <div className="text-gray-800 text-sm whitespace-pre-wrap">
        {clause.text}
      </div>
      
      {clause.recommendations && (
        <div className="mt-3 text-sm">
          <div className="font-medium text-gray-600 mb-1">Recommendations:</div>
          <div className="text-gray-700">{clause.recommendations}</div>
        </div>
      )}
      
      {clause.page_number && (
        <div className="mt-2 text-xs text-gray-500">
          Page {clause.page_number}
        </div>
      )}
    </div>
  );
};

export default ClauseHighlight;
