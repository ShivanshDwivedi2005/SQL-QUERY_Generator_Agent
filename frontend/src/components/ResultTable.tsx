import { Code } from 'lucide-react';
import { SQLViewer } from './SQLViewer';

interface ResultTableProps {
  sql?: string;
  summary?: string;
  isExpensive?: boolean;
  databaseAvailable?: boolean;
}

export function ResultTable({ sql, summary, isExpensive, databaseAvailable }: ResultTableProps) {
  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden animate-slide-up">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border bg-secondary/50">
        <div className="p-1.5 rounded-md bg-primary/10">
          <Code className="h-4 w-4 text-primary" />
        </div>
        <h3 className="font-semibold text-foreground text-sm">
          {databaseAvailable && !sql ? 'Answer' : 'Result'}
        </h3>
      </div>

      <div className="p-4">
        {databaseAvailable && !sql && summary ? (
          // Database mode: show paragraph answer for normal questions
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{summary}</p>
          </div>
        ) : sql ? (
          // SQL mode: show the query
          <SQLViewer sql={sql} isExpensive={isExpensive} />
        ) : (
          <div className="text-center py-8">
            <p className="text-sm text-muted-foreground">No result available</p>
          </div>
        )}
      </div>
    </div>
  );
}
