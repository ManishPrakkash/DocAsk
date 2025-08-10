from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalysisStrategy(ABC):
    """Abstract base class for document analysis strategies (Strategy Pattern)"""
    
    @abstractmethod
    def analyze(self, text: str, document_id: int) -> Dict[str, Any]:
        """Analyze document text and return structured results"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of this analysis strategy"""
        pass

class RuleBasedStrategy(AnalysisStrategy):
    """Rule-based analysis strategy using predefined patterns and rules"""
    
    def __init__(self):
        self.legal_patterns = self._initialize_legal_patterns()
        self.risk_keywords = self._initialize_risk_keywords()
    
    def get_strategy_name(self) -> str:
        return "rule_based"
    
    def analyze(self, text: str, document_id: int) -> Dict[str, Any]:
        """
        Analyze document using rule-based approach
        
        Args:
            text: Extracted document text
            document_id: Document ID for tracking
            
        Returns:
            Analysis results with clauses and metadata
        """
        logger.info(f"Starting rule-based analysis for document {document_id}")
        
        # Normalize text
        normalized_text = self._normalize_text(text)
        
        # Extract clauses using pattern matching
        clauses = self._extract_clauses(normalized_text)
        
        # Calculate risk scores and categorize
        analyzed_clauses = []
        for clause in clauses:
            analysis_result = self._analyze_clause(clause)
            analyzed_clauses.append(analysis_result)
        
        # Generate analysis summary
        summary = self._generate_analysis_summary(analyzed_clauses)
        
        return {
            'clauses': analyzed_clauses,
            'summary': summary,
            'metadata': {
                'strategy': self.get_strategy_name(),
                'analysis_date': datetime.utcnow().isoformat(),
                'total_text_length': len(text),
                'processed_clauses': len(analyzed_clauses)
            }
        }
    
    def _initialize_legal_patterns(self) -> Dict[str, List[str]]:
        """Initialize legal clause patterns for different categories"""
        return {
            'liability': [
                r'liable\s+for\s+any\s+damages',
                r'limitation\s+of\s+liability',
                r'shall\s+not\s+be\s+liable',
                r'indemnify\s+and\s+hold\s+harmless',
                r'gross\s+negligence',
                r'consequential\s+damages'
            ],
            'termination': [
                r'terminate\s+this\s+agreement',
                r'upon\s+termination',
                r'breach\s+of\s+contract',
                r'notice\s+of\s+termination',
                r'cure\s+period',
                r'immediate\s+termination'
            ],
            'payment': [
                r'payment\s+terms',
                r'invoice\s+date',
                r'late\s+payment',
                r'interest\s+on\s+overdue',
                r'payment\s+schedule',
                r'net\s+\d+\s+days'
            ],
            'intellectual_property': [
                r'intellectual\s+property\s+rights?',
                r'proprietary\s+information',
                r'trade\s+secrets?',
                r'copyright',
                r'patent',
                r'trademark'
            ],
            'confidentiality': [
                r'confidential\s+information',
                r'non-disclosure',
                r'proprietary\s+and\s+confidential',
                r'confidentiality\s+agreement',
                r'return\s+confidential\s+information'
            ],
            'governing_law': [
                r'governed\s+by\s+the\s+laws\s+of',
                r'jurisdiction\s+and\s+venue',
                r'dispute\s+resolution',
                r'arbitration',
                r'applicable\s+law'
            ]
        }
    
    def _initialize_risk_keywords(self) -> Dict[str, List[str]]:
        """Initialize risk assessment keywords"""
        return {
            'high_risk': [
                'unlimited liability', 'personal guarantee', 'liquidated damages',
                'punitive damages', 'immediate termination', 'no cure period',
                'waiver of rights', 'hold harmless', 'gross negligence'
            ],
            'medium_risk': [
                'indemnification', 'limitation of liability', 'consequential damages',
                'termination for convenience', 'change of control', 'assignment'
            ],
            'low_risk': [
                'standard terms', 'mutual agreement', 'reasonable efforts',
                'good faith', 'commercially reasonable'
            ]
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better pattern matching"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.lower().strip()
        return text
    
    def _extract_clauses(self, text: str) -> List[Dict[str, Any]]:
        """Extract potential legal clauses from text"""
        clauses = []
        sentences = self._split_into_sentences(text)
        
        for i, sentence in enumerate(sentences):
            if len(sentence.split()) < 5:  # Skip very short sentences
                continue
            
            # Check if sentence contains legal language
            if self._contains_legal_language(sentence):
                clause = {
                    'text': sentence.strip(),
                    'position': i,
                    'start_char': text.find(sentence),
                    'end_char': text.find(sentence) + len(sentence)
                }
                clauses.append(clause)
        
        return clauses
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - could be improved with NLP libraries
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _contains_legal_language(self, sentence: str) -> bool:
        """Check if sentence contains legal language patterns"""
        legal_indicators = [
            'shall', 'party', 'agreement', 'contract', 'terms',
            'conditions', 'liable', 'rights', 'obligations',
            'terminate', 'breach', 'indemnify', 'warrant'
        ]
        
        sentence_lower = sentence.lower()
        return any(indicator in sentence_lower for indicator in legal_indicators)
    
    def _analyze_clause(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual clause for category and risk"""
        text = clause['text']
        
        # Determine category
        category = self._categorize_clause(text)
        
        # Calculate risk score
        risk_score, risk_level = self._calculate_risk_score(text)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(text, category, risk_level)
        
        return {
            'text': text,
            'category': category,
            'subcategory': self._get_subcategory(text, category),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'confidence_score': self._calculate_confidence_score(text, category),
            'start_position': clause.get('start_char'),
            'end_position': clause.get('end_char'),
            'page_number': None,  # Would need document structure info
            'recommendations': recommendations,
            'metadata': {
                'analysis_method': 'rule_based',
                'matched_patterns': self._get_matched_patterns(text, category)
            }
        }
    
    def _categorize_clause(self, text: str) -> str:
        """Categorize clause based on content patterns"""
        text_lower = text.lower()
        
        for category, patterns in self.legal_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return category
        
        return 'general'
    
    def _get_subcategory(self, text: str, category: str) -> Optional[str]:
        """Get more specific subcategory if applicable"""
        text_lower = text.lower()
        
        subcategory_mapping = {
            'liability': {
                'limitation': ['limitation of liability', 'limited to'],
                'exclusion': ['shall not be liable', 'no liability'],
                'indemnification': ['indemnify', 'hold harmless']
            },
            'termination': {
                'for_cause': ['material breach', 'for cause'],
                'for_convenience': ['for convenience', 'without cause'],
                'automatic': ['automatic termination', 'immediately terminate']
            }
        }
        
        if category in subcategory_mapping:
            for subcat, keywords in subcategory_mapping[category].items():
                if any(keyword in text_lower for keyword in keywords):
                    return subcat
        
        return None
    
    def _calculate_risk_score(self, text: str) -> tuple[float, str]:
        """Calculate risk score and level for clause"""
        text_lower = text.lower()
        risk_score = 0.0
        
        # Check for high-risk keywords
        for keyword in self.risk_keywords['high_risk']:
            if keyword in text_lower:
                risk_score += 0.3
        
        # Check for medium-risk keywords  
        for keyword in self.risk_keywords['medium_risk']:
            if keyword in text_lower:
                risk_score += 0.2
        
        # Check for low-risk keywords (actually reduce risk)
        for keyword in self.risk_keywords['low_risk']:
            if keyword in text_lower:
                risk_score -= 0.1
        
        # Normalize score
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = 'critical'
        elif risk_score >= 0.5:
            risk_level = 'high'
        elif risk_score >= 0.3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return risk_score, risk_level
    
    def _calculate_confidence_score(self, text: str, category: str) -> float:
        """Calculate confidence in the categorization"""
        if category == 'general':
            return 0.3  # Low confidence for general category
        
        text_lower = text.lower()
        pattern_matches = 0
        total_patterns = len(self.legal_patterns.get(category, []))
        
        for pattern in self.legal_patterns.get(category, []):
            if re.search(pattern, text_lower):
                pattern_matches += 1
        
        if total_patterns == 0:
            return 0.5
        
        confidence = min(1.0, pattern_matches / total_patterns + 0.5)
        return confidence
    
    def _generate_recommendations(self, text: str, category: str, risk_level: str) -> str:
        """Generate recommendations based on clause analysis"""
        recommendations = []
        
        if risk_level in ['critical', 'high']:
            recommendations.append("⚠️ HIGH RISK: Review this clause carefully with legal counsel.")
        
        category_recommendations = {
            'liability': [
                "Consider adding mutual liability limitations",
                "Review indemnification scope and exclusions",
                "Ensure adequate insurance requirements"
            ],
            'termination': [
                "Verify termination notice periods are reasonable",
                "Check for adequate cure periods",
                "Review post-termination obligations"
            ],
            'payment': [
                "Confirm payment terms align with business practices",
                "Review late payment penalties",
                "Verify invoice and payment procedures"
            ],
            'confidentiality': [
                "Ensure confidentiality scope is appropriate",
                "Review return/destruction obligations",
                "Check for adequate exceptions"
            ]
        }
        
        if category in category_recommendations:
            recommendations.extend(category_recommendations[category][:2])  # Limit recommendations
        
        return " | ".join(recommendations) if recommendations else "No specific recommendations."
    
    def _get_matched_patterns(self, text: str, category: str) -> List[str]:
        """Get list of patterns that matched for this clause"""
        text_lower = text.lower()
        matched = []
        
        for pattern in self.legal_patterns.get(category, []):
            if re.search(pattern, text_lower):
                matched.append(pattern)
        
        return matched
    
    def _generate_analysis_summary(self, clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for the analysis"""
        if not clauses:
            return {
                'total_clauses': 0,
                'risk_distribution': {},
                'category_breakdown': {},
                'overall_risk_score': 0.0
            }
        
        risk_distribution = {}
        category_breakdown = {}
        total_risk_score = 0.0
        
        for clause in clauses:
            # Risk distribution
            risk_level = clause['risk_level']
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            # Category breakdown
            category = clause['category']
            category_breakdown[category] = category_breakdown.get(category, 0) + 1
            
            # Risk score accumulation
            total_risk_score += clause['risk_score']
        
        return {
            'total_clauses': len(clauses),
            'risk_distribution': risk_distribution,
            'category_breakdown': category_breakdown,
            'overall_risk_score': total_risk_score / len(clauses),
            'high_risk_clauses': sum(1 for c in clauses if c['risk_level'] in ['critical', 'high'])
        }

class MLModelStrategy(AnalysisStrategy):
    """Machine Learning-based analysis strategy (stubbed for future implementation)"""
    
    def get_strategy_name(self) -> str:
        return "ml_model"
    
    def analyze(self, text: str, document_id: int) -> Dict[str, Any]:
        """
        REFINEMENT_HOOK: implement_ml_model_analysis
        
        This is where we would implement ML-based document analysis:
        - Load trained models for clause classification
        - Use NLP libraries (spaCy, transformers) for entity extraction
        - Apply legal domain-specific models
        - Generate more accurate risk assessments
        """
        logger.info(f"ML-based analysis not yet implemented for document {document_id}")
        
        # For now, fall back to rule-based analysis
        rule_based = RuleBasedStrategy()
        result = rule_based.analyze(text, document_id)
        result['metadata']['strategy'] = self.get_strategy_name()
        result['metadata']['note'] = 'Using rule-based fallback - ML implementation pending'
        
        return result

class AnalysisService:
    """Main service for document analysis orchestration"""
    
    def __init__(self):
        self.strategies = {
            'rule_based': RuleBasedStrategy(),
            'ml_model': MLModelStrategy()
        }
        self.default_strategy = 'rule_based'
    
    def analyze_document(self, text: str, document_id: int, strategy_name: str = None) -> Dict[str, Any]:
        """
        Analyze document using specified or default strategy
        
        Args:
            text: Extracted document text
            document_id: Document ID for tracking
            strategy_name: Analysis strategy to use
            
        Returns:
            Analysis results
        """
        strategy_name = strategy_name or self.default_strategy
        strategy = self.strategies.get(strategy_name)
        
        if not strategy:
            logger.warning(f"Unknown strategy '{strategy_name}', using default")
            strategy = self.strategies[self.default_strategy]
        
        logger.info(f"Analyzing document {document_id} using {strategy.get_strategy_name()} strategy")
        
        try:
            result = strategy.analyze(text, document_id)
            result['metadata']['document_id'] = document_id
            result['metadata']['strategy_used'] = strategy.get_strategy_name()
            return result
        except Exception as e:
            logger.error(f"Analysis failed for document {document_id}: {str(e)}")
            raise
    
    def analyze_with_playbook(self, text: str, document_id: int, playbook_id: int) -> Dict[str, Any]:
        """
        REFINEMENT_HOOK: implement_playbook_comparison_logic
        
        Analyze document against specific legal playbook rules
        This would implement:
        - Load playbook rules from database
        - Apply custom rule sets to document analysis
        - Generate playbook-specific risk assessments
        - Highlight deviations from playbook standards
        """
        logger.info(f"Analyzing document {document_id} with playbook {playbook_id}")
        
        # For now, use standard analysis with playbook context
        result = self.analyze_document(text, document_id)
        result['metadata']['playbook_id'] = playbook_id
        result['metadata']['analysis_type'] = 'playbook_comparison'
        result['metadata']['note'] = 'Playbook comparison logic pending implementation'
        
        return result
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available analysis strategies"""
        return list(self.strategies.keys())
    
    def validate_analysis_request(self, text: str, document_id: int) -> bool:
        """Validate analysis request parameters"""
        if not text or not text.strip():
            logger.error(f"Empty text provided for document {document_id}")
            return False
        
        if len(text) < 50:  # Minimum text length
            logger.warning(f"Very short text for document {document_id}: {len(text)} characters")
        
        return True