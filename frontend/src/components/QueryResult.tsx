import { SQLViewer } from './SQLViewer';
import { Code } from 'lucide-react';

interface QueryResultProps {
  sql: string;
  isExpensive?: boolean;
}

export function QueryResult({ sql, isExpensive }: QueryResultProps) {
  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden animate-slide-up">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border bg-secondary/50">
        <div className="p-1.5 rounded-md bg-primary/10">
          <Code className="h-4 w-4 text-primary" />
        </div>
        <h3 className="font-semibold text-foreground text-sm">Query Result</h3>
      </div>

      <div className="p-4">
        <SQLViewer sql={sql} isExpensive={isExpensive} />
      </div>
    </div>
  );
}
