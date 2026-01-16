import { QueryStatus } from '@/types/query';
import { Brain, Search, Code, Play, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
  status: QueryStatus;
}

const loadingSteps = [
  { status: 'thinking', icon: Brain, label: 'Thinking…', sublabel: 'Analyzing your question' },
  { status: 'exploring', icon: Search, label: 'Exploring schema…', sublabel: 'Discovering tables and relationships' },
  { status: 'generating', icon: Code, label: 'Generating SQL…', sublabel: 'Building safe, optimized query' },
  { status: 'executing', icon: Play, label: 'Executing query…', sublabel: 'Running against database' },
];

export function LoadingState({ status }: LoadingStateProps) {
  const currentStepIndex = loadingSteps.findIndex((step) => step.status === status);

  return (
    <div className="flex flex-col items-center justify-center py-16 animate-fade-in">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl animate-pulse" />
        <div className="relative w-16 h-16 rounded-full bg-secondary border border-primary/30 flex items-center justify-center">
          <Loader2 className="h-8 w-8 text-primary animate-spin" />
        </div>
      </div>

      <div className="space-y-4 w-full max-w-xs">
        {loadingSteps.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStepIndex;
          const isComplete = index < currentStepIndex;
          const isPending = index > currentStepIndex;

          return (
            <div
              key={step.status}
              className={cn(
                'flex items-center gap-3 p-3 rounded-lg transition-all duration-300',
                isActive && 'bg-primary/10 border border-primary/30',
                isComplete && 'opacity-60',
                isPending && 'opacity-30'
              )}
            >
              <div
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center transition-all',
                  isActive && 'bg-primary text-primary-foreground',
                  isComplete && 'bg-primary/20 text-primary',
                  isPending && 'bg-muted text-muted-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
              </div>
              <div>
                <p className={cn('text-sm font-medium', isActive && 'text-primary')}>
                  {step.label}
                </p>
                <p className="text-xs text-muted-foreground">{step.sublabel}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
