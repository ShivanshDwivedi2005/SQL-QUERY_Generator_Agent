import { useState, useCallback } from 'react';
import { QueryStatus, QueryResponse } from '@/types/query';
import { askQuestion, AskResponse } from '@/services/api';

export function useQuerySimulation() {
  const [status, setStatus] = useState<QueryStatus>('idle');
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');

  const runQuery = useCallback(async (query: string) => {
    setCurrentQuery(query);
    setResponse(null);
    setStatus('thinking');

    try {
      // Call backend API
      const apiResponse = await askQuestion(query, true);

      if (!apiResponse.success) {
        const databaseAvailable = apiResponse.databaseAvailable || false;
        const isSqlRequest = apiResponse.isSqlRequest || false;
        
        let showReasoningTrace = true;
        let showResult = true;
        
        if (!databaseAvailable) {
          if (isSqlRequest) {
            showReasoningTrace = false;
            showResult = true;
          } else {
            showReasoningTrace = true;
            showResult = false;
          }
        }

        setStatus('error');
        setResponse({
          reasoning: [],
          sql: apiResponse.sql || '',
          result: { columns: [], rows: [] },
          summary: apiResponse.error || apiResponse.summary || 'An error occurred while processing your question',
          status: 'error',
          error: apiResponse.error,
          isExpensive: false,
          databaseAvailable,
          isSqlRequest,
          showReasoningTrace,
          showResult,
        });
        return;
      }

      // Determine visibility based on conditions:
      // IF database exists: 
      //   - Normal questions: show only answer in result (paragraph format)
      //   - SQL request: show SQL in result
      // IF no database:
      //   - If SQL requested: show only result (SQL)
      //   - If normal question: show only reasoning trace (2-liner answer)
      const databaseAvailable = apiResponse.databaseAvailable || false;
      const isSqlRequest = apiResponse.isSqlRequest || false;
      
      let showReasoningTrace = false;
      let showResult = true;
      
      if (!databaseAvailable) {
        // No database: use API mode
        if (isSqlRequest) {
          // SQL request: show only SQL
          showReasoningTrace = false;
          showResult = true;
        } else {
          // Normal question: show only 2-line reasoning
          showReasoningTrace = true;
          showResult = false;
        }
      } else {
        // Database available: always show result (paragraph answer or SQL)
        showReasoningTrace = false;
        showResult = true;
      }
      // If database available: show both (defaults to true above)

      // Transform API response to match frontend QueryResponse format
      const reasoning = Array.isArray(apiResponse.reasoning) 
        ? apiResponse.reasoning.map((step: any, index: number) => ({
            id: `step-${index}`,
            label: step.label || step.step || `Step ${index + 1}`,
            detail: step.detail || '',
            status: 'complete' as const,
          }))
        : [];

      const sql = apiResponse.sql || '';
      const columns = apiResponse.result?.columns || [];
      const rows = apiResponse.result?.rows || [];

      // Determine response status
      let responseStatus: QueryStatus = (apiResponse.status as QueryStatus) || 'success';
      if (rows.length === 0 && sql) {
        responseStatus = 'empty';
      }

      setResponse({
        reasoning,
        sql,
        result: { columns, rows },
        summary: apiResponse.summary || 'Query completed successfully',
        status: responseStatus,
        isExpensive: false,
        databaseAvailable,
        isSqlRequest,
        showReasoningTrace,
        showResult,
      });

      setStatus(responseStatus);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      setStatus('error');
      setResponse({
        reasoning: [],
        sql: '',
        result: { columns: [], rows: [] },
        summary: errorMessage,
        status: 'error',
        error: errorMessage,
        isExpensive: false,
        databaseAvailable: false,
        isSqlRequest: false,
        showReasoningTrace: false,
        showResult: false,
      });
    }
  }, []);

  const reset = useCallback(() => {
    setStatus('idle');
    setResponse(null);
    setCurrentQuery('');
  }, []);

  return {
    status,
    response,
    currentQuery,
    runQuery,
    reset,
  };
}
