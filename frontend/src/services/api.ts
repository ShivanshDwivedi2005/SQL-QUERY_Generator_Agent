/**
 * API service for communicating with the backend
 */

// const API_BASE_URL = 'https://ai-sql-agent-4.onrender.com';
export const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';
export const MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024;

export interface HealthResponse {
  status: string;
  agent_initialized: boolean;
  database_available: boolean;
  database_provider: string;
}

export interface AskResponse {
  success: boolean;
  question?: string;
  summary?: string;
  last_result?: {
    sql?: string;
    columns?: string[];
    rows?: Record<string, unknown>[];
    success?: boolean;
    error?: string;
  };
  reasoning_steps?: Array<{
    step: string;
    detail: string;
    icon: string;
  }>;
  reasoning?: Array<{
    step?: string;
    label?: string;
    detail: string;
  }>;
  result?: {
    columns?: string[];
    rows?: Record<string, unknown>[];
  };
  sql?: string;
  status?: string;
  databaseAvailable?: boolean;
  isSqlRequest?: boolean;
  error?: string;
}

export async function askQuestion(question: string, showReasoning: boolean = true): Promise<AskResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        show_reasoning: showReasoning,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to communicate with backend';
    console.error('API Error:', errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  }
}

export interface DatabaseInfo {
  databases: string[];
  current: string | null;
  provider?: string;
  connected: boolean;
}

export async function getHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching health:', error);
    return null;
  }
}

export async function listDatabases(): Promise<DatabaseInfo> {
  try {
    const response = await fetch(`${API_BASE_URL}/databases`);
    if (!response.ok) {
      throw new Error(`Failed to fetch databases: ${response.statusText}`);
    }
    const data = await response.json();
    return {
      databases: data.databases ?? [],
      current: data.current ?? null,
      provider: data.provider ?? 'neon',
      connected: Boolean(data.connected),
    };
  } catch (error) {
    console.error('Error listing databases:', error);
    return { databases: [], current: null, provider: 'neon', connected: false };
  }
}

/** Load DB metadata and connection status; /health is authoritative for connected. */
export async function fetchConnectionStatus(): Promise<DatabaseInfo> {
  const [health, databases] = await Promise.all([getHealth(), listDatabases()]);
  const connected = health?.database_available ?? databases.connected;

  return {
    ...databases,
    connected,
    current: connected
      ? databases.current ?? databases.databases[0] ?? null
      : databases.current,
  };
}

export interface DatabaseColumn {
  name: string;
  type: string;
  notnull: boolean;
  default_value: string | null;
  pk: boolean;
}

export interface DatabaseTable {
  name: string;
  columns: DatabaseColumn[];
  row_count: number;
  sample_data: Record<string, unknown>[];
}

export interface DatabaseView {
  database: string;
  dialect?: string;
  tables: DatabaseTable[];
}

export async function viewDatabase(): Promise<DatabaseView> {
  try {
    const response = await fetch(`${API_BASE_URL}/database/view`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to view database: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error viewing database:', error);
    throw error;
  }
}

export interface UploadDataResponse {
  success: boolean;
  table?: string;
  columns?: string[];
  rows_inserted?: number;
  message?: string;
  error?: string;
}

export async function uploadData(file: File): Promise<UploadDataResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload-data`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to upload data: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to upload data';
    console.error('Data upload error:', errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  }
}

export interface ExecuteSQLResponse {
  success: boolean;
  sql?: string;
  result?: {
    columns: string[];
    rows: Record<string, unknown>[];
  };
  status?: string;
  message?: string;
  error?: string;
}

export async function executeRawSQL(sqlQuery: string): Promise<ExecuteSQLResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/execute-sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: sqlQuery,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to execute SQL';
    console.error('SQL Execution Error:', errorMessage);
    return {
      success: false,
      error: errorMessage,
    };
  }
}
