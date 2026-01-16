export type QueryStatus = 'idle' | 'thinking' | 'exploring' | 'generating' | 'executing' | 'success' | 'empty' | 'error' | 'ambiguous';

export interface ReasoningStep {
  id: string;
  label: string;
  detail: string;
  status: 'pending' | 'active' | 'complete';
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface QueryResponse {
  reasoning: ReasoningStep[];
  sql: string;
  result: QueryResult;
  summary: string;
  status: QueryStatus;
  clarification?: string;
  error?: string;
  isExpensive?: boolean;
  databaseAvailable?: boolean;
  isSqlRequest?: boolean;
  showReasoningTrace?: boolean;
  showResult?: boolean;
}

export interface ExampleQuery {
  label: string;
  query: string;
  category: 'simple' | 'moderate' | 'reasoning' | 'ambiguous' | 'meta';
}
