import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Play, Loader2, Code2 } from 'lucide-react';
import { executeRawSQL, ExecuteSQLResponse } from '@/services/api';
import { ResultTable } from './ResultTable';

export function SQLEditor() {
  const [sqlQuery, setSqlQuery] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<ExecuteSQLResponse | null>(null);

  const handleExecute = async () => {
    if (!sqlQuery.trim()) return;

    setIsExecuting(true);
    setResult(null);

    try {
      const response = await executeRawSQL(sqlQuery);
      setResult(response);
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Failed to execute query',
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl/Cmd + Enter to execute
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleExecute();
    }
  };

  return (
    <div className="grid lg:grid-cols-2 gap-6 h-full">
      {/* Left Panel - SQL Editor */}
      <div>
        <div className="bg-card rounded-xl border border-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Code2 className="h-5 w-5 text-primary" />
              SQL Editor
            </h2>
            <span className="text-xs text-muted-foreground">
              Press Ctrl+Enter to execute
            </span>
          </div>

          <div className="space-y-3">
            <Textarea
              value={sqlQuery}
              onChange={(e) => setSqlQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter your SQL query here...&#10;&#10;Example:&#10;SELECT * FROM users LIMIT 10;"
              className="font-mono text-sm min-h-[400px] resize-y"
              disabled={isExecuting}
            />

            <div className="flex justify-end">
              <Button
                onClick={handleExecute}
                disabled={!sqlQuery.trim() || isExecuting}
                className="gap-2"
              >
                {isExecuting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Execute Query
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Results */}
      <div className="space-y-4 lg:max-h-[calc(100vh-140px)] lg:overflow-y-auto lg:pr-2">
        {!result ? (
          <div className="bg-muted/30 rounded-lg border border-border p-8 text-center h-full flex items-center justify-center">
            <div>
              <Code2 className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground text-sm">
                Query results will appear here
              </p>
            </div>
          </div>
        ) : (
          <div className="animate-slide-up">
            {result.error ? (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <div className="text-destructive text-sm font-medium">Error:</div>
                  <div className="text-destructive text-sm flex-1">{result.error}</div>
                </div>
              </div>
            ) : (
              <>
                {result.message && (
                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 mb-4">
                    <p className="text-sm text-primary">{result.message}</p>
                  </div>
                )}
                <ResultTable
                  sql={result.sql}
                  columns={result.result?.columns || []}
                  rows={result.result?.rows || []}
                  databaseAvailable={true}
                />
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
