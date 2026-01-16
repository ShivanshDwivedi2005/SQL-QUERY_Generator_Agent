import { Header } from '@/components/Header';
import { QueryInput } from '@/components/QueryInput';
import { LoadingState } from '@/components/LoadingState';
import { ReasoningPanel } from '@/components/ReasoningPanel';
import { ResultTable } from '@/components/ResultTable';
import { StatusBanner } from '@/components/StatusBanner';
import { EmptyState } from '@/components/EmptyState';
import { useQuerySimulation } from '@/hooks/useQuerySimulation';

const Index = () => {
  const { status, response, currentQuery, runQuery, reset } = useQuerySimulation();
  const isLoading = ['thinking', 'exploring', 'generating', 'executing'].includes(status);
  const hasResponse = response !== null;

  const handleDatabaseChange = () => {
    // Reset query state when database changes
    reset();
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header onDatabaseChange={handleDatabaseChange} />
      
      <main className="flex-1 container mx-auto px-4 py-6">
        <div className="grid lg:grid-cols-2 gap-6 h-full">
          {/* Left Panel - User Interaction */}
          <div className="space-y-6">
            <div className="bg-card rounded-xl border border-border p-6">
              <h2 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary" />
                Your Question
              </h2>
              <QueryInput onSubmit={runQuery} status={status} />
            </div>

            {/* Current query display */}
            {currentQuery && (
              <div className="bg-secondary/50 rounded-lg border border-border p-4 animate-fade-in">
                <p className="text-sm text-muted-foreground mb-1">Currently processing:</p>
                <p className="text-foreground font-medium">"{currentQuery}"</p>
              </div>
            )}

            {/* Mobile: Show loading state */}
            <div className="lg:hidden">
              {isLoading && <LoadingState status={status} />}
            </div>
          </div>

          {/* Right Panel - Results and Reasoning */}
          <div className="space-y-4 lg:max-h-[calc(100vh-140px)] lg:overflow-y-auto lg:pr-2">
            {/* Loading state (desktop) */}
            {isLoading && (
              <div className="hidden lg:block">
                <LoadingState status={status} />
              </div>
            )}

            {/* Empty state */}
            {status === 'idle' && !hasResponse && <EmptyState />}

            {/* Results */}
            {hasResponse && !isLoading && (
              <>
                <StatusBanner
                  status={status}
                  clarification={response.clarification}
                  error={response.error}
                  onRetry={reset}
                />

                {/* Reasoning Trace - 2 key points (shown when database available or normal question without DB) */}
                {response.showReasoningTrace && response.summary && (
                  <ReasoningPanel summary={response.summary} sql={response.sql} />
                )}

                {/* Result Block - SQL query (shown when database available or SQL requested without DB) */}
                {response.showResult && (
                  <ResultTable 
                    sql={response.sql}
                    summary={response.summary}
                    isExpensive={response.isExpensive}
                    databaseAvailable={response.databaseAvailable}
                  />
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
