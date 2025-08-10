// TypeScript interfaces that mirror backend Pydantic schemas for end-to-end type safety

export enum DocumentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETE = 'complete',
  ERROR = 'error'
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// User types
export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

// Document types
export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  status: DocumentStatus;
  file_size?: number;
  created_at: string;
  total_clauses_found: number;
  processing_completed_at?: string;
  error_message?: string;
}

export interface DocumentStatusUpdate {
  id: number;
  status: DocumentStatus;
  progress?: number;
  error_message?: string;
  total_clauses_found: number;
}

export interface UploadResponse {
  message: string;
  document_id: number;
  status: DocumentStatus;
  job_id?: string;
}

// Clause types
export interface Clause {
  id: number;
  text: string;
  category: string;
  subcategory?: string;
  risk_score: number;
  risk_level: RiskLevel;
  confidence_score: number;
  start_position?: number;
  end_position?: number;
  page_number?: number;
  recommendations?: string;
}

// Analysis types
export interface AnalysisResult {
  document_id: number;
  total_clauses: number;
  risk_distribution: Record<string, number>;
  category_breakdown: Record<string, number>;
  recommendations: string[];
  overall_risk_score: number;
  analysis_metadata: Record<string, any>;
}

export interface DocumentAnalysis {
  document: Document;
  clauses: Clause[];
  analysis_summary: AnalysisResult;
}

// Legal Playbook types
export interface LegalPlaybook {
  id: number;
  name: string;
  description?: string;
  rules: Record<string, any>;
  version: string;
  is_active: string;
  created_at: string;
}

export interface LegalPlaybookCreate {
  name: string;
  description?: string;
  rules: Record<string, any>;
}

export interface LegalPlaybookResponse {
  id: number;
  name: string;
  description?: string;
  version: string;
  is_active: string;
  created_at: string;
}

// Analysis request types
export interface AnalysisRequest {
  document_id: number;
  playbook_id?: number;
  analysis_type: string;
}

// Job status types
export interface JobStatus {
  job_id: string;
  state: string;
  progress: number;
  status: string;
  result?: any;
  error?: string;
}

// Statistics types
export interface AnalysisStatistics {
  summary: {
    total_documents: number;
    total_clauses: number;
    average_risk_score: number;
  };
  document_status: Record<string, number>;
  risk_distribution: Record<string, number>;
  category_breakdown: Record<string, number>;
}

// API Error types
export interface APIError {
  detail: string;
  code?: string;
  timestamp?: string;
}

// Component prop types
export interface DocumentCardProps {
  document: Document;
  onView: (id: number) => void;
  onDelete: (id: number) => void;
}

export interface ClauseHighlightProps {
  clause: Clause;
  isSelected: boolean;
  onClick: () => void;
}

export interface RiskBadgeProps {
  riskLevel: RiskLevel;
  riskScore: number;
  size?: 'sm' | 'md' | 'lg';
}

// State management types
export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
}

export interface DocumentState {
  documents: Document[];
  currentDocument: DocumentAnalysis | null;
  isLoading: boolean;
  uploadProgress: number;
  fetchDocuments: () => Promise<void>;
  uploadDocument: (file: File) => Promise<number>;
  fetchDocumentAnalysis: (id: number) => Promise<void>;
  pollDocumentStatus: (id: number) => Promise<DocumentStatusUpdate>;
  deleteDocument: (id: number) => Promise<void>;
}

export interface PlaybookState {
  playbooks: LegalPlaybookResponse[];
  currentPlaybook: LegalPlaybook | null;
  isLoading: boolean;
  fetchPlaybooks: () => Promise<void>;
  createPlaybook: (data: LegalPlaybookCreate) => Promise<void>;
  updatePlaybook: (id: number, data: Partial<LegalPlaybookCreate>) => Promise<void>;
  deletePlaybook: (id: number) => Promise<void>;
  fetchPlaybook: (id: number) => Promise<void>;
}