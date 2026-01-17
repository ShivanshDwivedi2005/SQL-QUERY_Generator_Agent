import { Code, CheckCircle2, Table, Database } from 'lucide-react';
import { SQLViewer } from './SQLViewer';
import {
  Table as UITable,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface ResultTableProps {
  sql?: string;
  summary?: string;
  isExpensive?: boolean;
  databaseAvailable?: boolean;
  columns?: string[];
  rows?: Record<string, any>[];
}

export function ResultTable({ sql, summary, isExpensive, databaseAvailable, columns = [], rows = [] }: ResultTableProps) {
  const hasResults = columns.length > 0 && rows.length > 0;

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

      <div className="p-4 space-y-4">
        {databaseAvailable && !sql && summary ? (
          // Database mode: show paragraph answer for normal questions
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{summary}</p>
          </div>
        ) : sql ? (
          // SQL mode: show the query
          <>
            <SQLViewer sql={sql} isExpensive={isExpensive} />
            
            {/* Output count summary - shown right after SQL query */}
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 flex items-center gap-3">
              <Database className="h-5 w-5 text-primary flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">
                  {hasResults ? (
                    <>
                      Query executed successfully • {rows.length} row{rows.length !== 1 ? 's' : ''} returned
                      {columns.length > 0 && <> • {columns.length} column{columns.length !== 1 ? 's' : ''}</>}
                    </>
                  ) : (
                    <>Query executed successfully • No rows returned</>
                  )}
                </p>
              </div>
            </div>
            
            {/* Show data table if we have results */}
            {hasResults && (
              <div className="mt-4">
                <div className="flex items-center gap-2 mb-3">
                  <Table className="h-4 w-4 text-muted-foreground" />
                  <h4 className="text-sm font-medium text-foreground">
                    Query Results
                  </h4>
                </div>
                <div className="border border-border rounded-lg overflow-hidden">
                  <div className="max-h-96 overflow-auto">
                    <UITable>
                      <TableHeader className="sticky top-0 bg-secondary z-10">
                        <TableRow>
                          {columns.map((column) => (
                            <TableHead key={column} className="font-semibold text-xs">
                              {column}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {rows.map((row, idx) => (
                          <TableRow key={idx}>
                            {columns.map((column) => (
                              <TableCell key={column} className="text-sm">
                                {row[column] !== null && row[column] !== undefined
                                  ? String(row[column])
                                  : <span className="text-muted-foreground italic">null</span>}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </UITable>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8">
            <p className="text-sm text-muted-foreground">No result available</p>
          </div>
        )}
      </div>
    </div>
  );
}
