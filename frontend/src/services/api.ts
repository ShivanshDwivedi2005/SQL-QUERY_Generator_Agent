/**
 * API service for communicating with the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload-database`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to upload database: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error uploading database:', error);
    throw error;
  }
}
