import { useState } from 'react';
import { Code, Copy, Check, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface SQLViewerProps {
  sql: string;
  isExpensive?: boolean;
}

// Simple SQL syntax highlighting
function highlightSQL(sql: string): React.ReactNode[] {
  const keywords = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|EXISTS|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|AS|DISTINCT|COUNT|SUM|AVG|MAX|MIN|ROUND|NULL|IS|DESC|ASC|UNION|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TABLE|INDEX|PRIMARY|KEY|FOREIGN|REFERENCES|CASCADE|SET|VALUES)\b/gi;
  const strings = /'[^']*'/g;
  const comments = /--.*$/gm;
  const numbers = /\b\d+\.?\d*\b/g;

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  const tokens: { start: number; end: number; type: string; text: string }[] = [];

  // Collect all tokens
  sql.replace(keywords, (match, _, offset) => {
    tokens.push({ start: offset, end: offset + match.length, type: 'keyword', text: match });
    return match;
  });
  sql.replace(strings, (match, offset) => {
    tokens.push({ start: offset, end: offset + match.length, type: 'string', text: match });
    return match;
  });
  sql.replace(comments, (match, offset) => {
    tokens.push({ start: offset, end: offset + match.length, type: 'comment', text: match });
    return match;
  });
  sql.replace(numbers, (match, offset) => {
    tokens.push({ start: offset, end: offset + match.length, type: 'number', text: match });
    return match;
  });

  // Sort by position and filter overlaps
  tokens.sort((a, b) => a.start - b.start);
  const filtered: typeof tokens = [];
  for (const token of tokens) {
    if (filtered.length === 0 || token.start >= filtered[filtered.length - 1].end) {
      filtered.push(token);
    }
  }

  // Build parts
  for (const token of filtered) {
    if (token.start > lastIndex) {
      parts.push(sql.slice(lastIndex, token.start));
    }
    const className = {
      keyword: 'text-primary font-medium',
      string: 'text-green-400',
      comment: 'text-muted-foreground italic',
      number: 'text-orange-400',
    }[token.type];
    parts.push(
      <span key={token.start} className={className}>
        {token.text}
      </span>
    );
    lastIndex = token.end;
  }
  if (lastIndex < sql.length) {
    parts.push(sql.slice(lastIndex));
  }

  return parts;
}

export function SQLViewer({ sql, isExpensive }: SQLViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = sql;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (fallbackErr) {
        console.error('Fallback copy failed:', fallbackErr);
      }
      document.body.removeChild(textArea);
    }
  };

  if (!sql) return null;

  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden animate-slide-up">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-secondary/50">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-code-bg">
            <Code className="h-4 w-4 text-primary" />
          </div>
          <h3 className="font-semibold text-foreground text-sm">Generated SQL</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 px-2 text-xs"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 mr-1 text-primary" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </>
          )}
        </Button>
      </div>

      {isExpensive && (
        <div className="px-4 py-2 bg-warning/10 border-b border-warning/20 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-warning" />
          <span className="text-sm text-warning">
            This query may be slow on large datasets
          </span>
        </div>
      )}

      <div className="p-4 bg-code-bg overflow-x-auto">
        <pre className="text-sm font-mono leading-relaxed text-foreground/90 whitespace-pre-wrap">
          <code>{highlightSQL(sql)}</code>
        </pre>
      </div>
    </div>
  );
}
