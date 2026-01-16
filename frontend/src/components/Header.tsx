import { Database, Sparkles } from 'lucide-react';
import { DatabaseManager } from './DatabaseManager';

interface HeaderProps {
  onDatabaseChange?: () => void;
}

export function Header({ onDatabaseChange }: HeaderProps) {
  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/30 blur-lg rounded-lg" />
            <div className="relative p-2 rounded-lg bg-secondary border border-primary/30">
              <Database className="h-6 w-6 text-primary" />
            </div>
          </div>
          <div>
            <h1 className="text-lg font-bold text-foreground flex items-center gap-2">
              Ask Your Database
              <Sparkles className="h-4 w-4 text-primary" />
            </h1>
            <p className="text-xs text-muted-foreground">
              Natural language → SQL with reasoning
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <DatabaseManager onDatabaseChange={onDatabaseChange} />
        </div>
      </div>
    </header>
  );
}
