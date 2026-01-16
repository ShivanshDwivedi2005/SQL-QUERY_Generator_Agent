import { QueryStatus } from '@/types/query';
import { AlertCircle, HelpCircle, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatusBannerProps {
  status: QueryStatus;
  clarification?: string;
  error?: string;
  onRetry?: () => void;
}

export function StatusBanner({ status, clarification, error, onRetry }: StatusBannerProps) {
  if (status === 'ambiguous' && clarification) {
    return (
      <div className="bg-warning/10 border border-warning/30 rounded-lg p-4 animate-slide-up">
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded-md bg-warning/20">
            <HelpCircle className="h-5 w-5 text-warning" />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-warning mb-2">Clarification Needed</h4>
            <p className="text-sm text-foreground/80 whitespace-pre-line leading-relaxed">
              {clarification}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'error' && error) {
    return (
      <div className="bg-destructive/10 border border-destructive/30 rounded-lg p-4 animate-slide-up">
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded-md bg-destructive/20">
            <XCircle className="h-5 w-5 text-destructive" />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-destructive mb-2">Query Error</h4>
            <p className="text-sm text-foreground/80 mb-3">{error}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="text-sm font-medium text-primary hover:underline"
              >
                Try a different approach →
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (status === 'empty') {
    return (
      <div className="bg-muted/50 border border-border rounded-lg p-4 animate-slide-up">
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded-md bg-muted">
            <AlertCircle className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <h4 className="font-medium text-foreground mb-1">Empty Result</h4>
            <p className="text-sm text-muted-foreground">
              The query executed successfully but returned no matching data.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="bg-primary/10 border border-primary/30 rounded-lg p-4 animate-slide-up">
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-md bg-primary/20">
            <CheckCircle2 className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h4 className="font-medium text-primary">Query Successful</h4>
            <p className="text-sm text-muted-foreground">
              Results are displayed below
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
