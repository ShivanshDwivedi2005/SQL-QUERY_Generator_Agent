/**
 * API service for communicating with the backend
 */

const API_BASE_URL = 'https://ai-sql-agent-4.onrender.com';

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
}

export async function listDatabases(): Promise<DatabaseInfo> {
  try {
    const response = await fetch(`${API_BASE_URL}/databases`);
    if (!response.ok) {
      throw new Error(`Failed to fetch databases: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error listing databases:', error);
    return { databases: [], current: null };
  }
}

export async function selectDatabase(dbName: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/databases/${dbName}/select`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to select database: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error selecting database:', error);
    throw error;
  }
}

export async function uploadDatabase(file: File): Promise<{ success: boolean; message: string; database: string }> {
  try {
    console.log('Starting upload for file:', file.name);
    console.log('API URL:', API_BASE_URL);
    
    const formData = new FormData();
    formData.append('file', file);

    console.log('Sending request to:', `${API_BASE_URL}/upload-database`);

    const response = await fetch(`${API_BASE_URL}/upload-database`, {
      method: 'POST',
      body: formData,
    });

    console.log('Response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Upload failed:', errorData);
      throw new Error(errorData.detail || `Failed to upload database: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('Upload successful:', result);
    return result;
  } catch (error) {
    console.error('Error uploading database:', error);
    throw error;
  }
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
