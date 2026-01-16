import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { exampleQueries } from '@/data/mockResponses';
import { QueryStatus } from '@/types/query';
import { cn } from '@/lib/utils';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  status: QueryStatus;
}

const categoryColors: Record<string, string> = {
  simple: 'bg-primary/10 text-primary border-primary/20 hover:bg-primary/20',
  moderate: 'bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20',
  reasoning: 'bg-purple-500/10 text-purple-400 border-purple-500/20 hover:bg-purple-500/20',
  ambiguous: 'bg-warning/10 text-warning border-warning/20 hover:bg-warning/20',
  meta: 'bg-muted text-muted-foreground border-border hover:bg-secondary',
};

export function QueryInput({ onSubmit, status }: QueryInputProps) {
  const [query, setQuery] = useState('');
  const isLoading = ['thinking', 'exploring', 'generating', 'executing'].includes(status);

  const handleSubmit = () => {
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="space-y-6">
      <div className="relative">
        <Textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your database..."
          className="min-h-[120px] resize-none bg-secondary border-border text-foreground placeholder:text-muted-foreground pr-14 text-base focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
          disabled={isLoading}
        />
        <Button
          onClick={handleSubmit}
          disabled={!query.trim() || isLoading}
          size="icon"
          className="absolute bottom-3 right-3 glow-primary-sm"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Sparkles className="h-4 w-4 text-primary" />
          <span>Try an example</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((example) => (
            <button
              key={example.label}
              onClick={() => {
                setQuery(example.query);
                onSubmit(example.query);
              }}
              disabled={isLoading}
              className={cn(
                'px-3 py-1.5 text-sm rounded-full border transition-all',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                categoryColors[example.category]
              )}
            >
              {example.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
