import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, AlertTriangle, TrendingUp, BarChart3 } from 'lucide-react';
import { useDocumentStore } from '@/stores/documentStore';
import { Clause, RiskLevel } from '@/types';
import LoadingSpinner from '../ui/LoadingSpinner';
import RiskBadge from '../ui/RiskBadge';
import ClauseHighlight from './ClauseHighlight';

const AnalysisView: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const { currentDocument, isLoading, fetchDocumentAnalysis } = useDocumentStore();
  const [selectedClause, setSelectedClause] = useState<Clause | null>(null);
  const [filterByRisk, setFilterByRisk] = useState<RiskLevel | 'all'>('all');
  const [filterByCategory, setFilterByCategory] = useState<string>('all');

  useEffect(() => {
    if (documentId) {
      fetchDocumentAnalysis(parseInt(documentId));
    }
  }, [documentId, fetchDocumentAnalysis]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!currentDocument) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Document not found</h3>
        <p className="text-gray-600 mb-6">
          The requested document could not be found or is not yet analyzed.
        </p>
        <button
          onClick={() => navigate('/dashboard')}
          className="btn-primary"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </button>
      </div>
    );
  }

  const { document, clauses, analysis_summary } = currentDocument;

  // Filter clauses
  const filteredClauses = clauses.filter(clause => {
    const riskMatch = filterByRisk === 'all' || clause.risk_level === filterByRisk;
    const categoryMatch = filterByCategory === 'all' || clause.category === filterByCategory;
    return riskMatch && categoryMatch;
  });

  // Get unique categories
  const categories = [...new Set(clauses.map(clause => clause.category))];

  const getRiskColor = (riskLevel: RiskLevel): string => {
    switch (riskLevel) {
      case RiskLevel.LOW: return 'text-green-600';
      case RiskLevel.MEDIUM: return 'text-yellow-600';
      case RiskLevel.HIGH: return 'text-red-600';
      case RiskLevel.CRITICAL: return 'text-red-800';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{document.original_filename}</h1>
            <p className="text-gray-600">Document Analysis Results</p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-gray-600">Overall Risk Score</p>
            <p className={`text-2xl font-bold ${getRiskColor(
              analysis_summary.overall_risk_score >= 0.7 ? RiskLevel.CRITICAL :
              analysis_summary.overall_risk_score >= 0.5 ? RiskLevel.HIGH :
              analysis_summary.overall_risk_score >= 0.3 ? RiskLevel.MEDIUM : RiskLevel.LOW
            )}`}>
              {(analysis_summary.overall_risk_score * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Analysis Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-semibold text-gray-900">{analysis_summary.total_clauses}</p>
              <p className="text-sm text-gray-600">Total Clauses</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-semibold text-gray-900">
                {(analysis_summary.risk_distribution.high || 0) + (analysis_summary.risk_distribution.critical || 0)}
              </p>
              <p className="text-sm text-gray-600">High Risk</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-semibold text-gray-900">
                {analysis_summary.risk_distribution.low || 0}
              </p>
              <p className="text-sm text-gray-600">Low Risk</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100">
              <BarChart3 className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-semibold text-gray-900">{categories.length}</p>
              <p className="text-sm text-gray-600">Categories</p>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Distribution */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(analysis_summary.risk_distribution).map(([risk, count]) => (
            <div key={risk} className="text-center">
              <div className={`text-2xl font-bold ${getRiskColor(risk as RiskLevel)}`}>
                {count}
              </div>
              <div className="text-sm text-gray-600 capitalize">{risk} Risk</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clauses List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Identified Clauses</h3>
                <div className="flex space-x-4">
                  {/* Risk Filter */}
                  <select
                    value={filterByRisk}
                    onChange={(e) => setFilterByRisk(e.target.value as RiskLevel | 'all')}
                    className="text-sm border border-gray-300 rounded-md px-3 py-1"
                  >
                    <option value="all">All Risk Levels</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>

                  {/* Category Filter */}
                  <select
                    value={filterByCategory}
                    onChange={(e) => setFilterByCategory(e.target.value)}
                    className="text-sm border border-gray-300 rounded-md px-3 py-1"
                  >
                    <option value="all">All Categories</option>
                    {categories.map(category => (
                      <option key={category} value={category}>
                        {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {filteredClauses.map((clause) => (
                <ClauseHighlight
                  key={clause.id}
                  clause={clause}
                  isSelected={selectedClause?.id === clause.id}
                  onClick={() => setSelectedClause(clause)}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Clause Details Sidebar */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Clause Details</h3>
            
            {selectedClause ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Risk Level</label>
                  <RiskBadge riskLevel={selectedClause.risk_level} riskScore={selectedClause.risk_score} />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <p className="text-sm text-gray-900 capitalize">
                    {selectedClause.category.replace('_', ' ')}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Confidence Score</label>
                  <p className="text-sm text-gray-900">
                    {(selectedClause.confidence_score * 100).toFixed(1)}%
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Clause Text</label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {selectedClause.text}
                  </p>
                </div>

                {selectedClause.recommendations && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Recommendations</label>
                    <div className="text-sm text-gray-900 bg-yellow-50 p-3 rounded-md">
                      {selectedClause.recommendations.split(' | ').map((rec, index) => (
                        <div key={index} className="mb-2 last:mb-0">
                          • {rec}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-600 text-sm">
                Select a clause from the list to view detailed analysis and recommendations.
              </p>
            )}
          </div>

          {/* Overall Recommendations */}
          {analysis_summary.recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Recommendations</h3>
              <div className="space-y-3">
                {analysis_summary.recommendations.slice(0, 5).map((rec, index) => (
                  <div key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-1.5 h-1.5 bg-primary-600 rounded-full mt-2 mr-3" />
                    <p className="text-sm text-gray-700">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalysisView;