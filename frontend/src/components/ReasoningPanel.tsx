import { Brain, Check } from 'lucide-react';

interface ReasoningPanelProps {
  summary?: string;
  sql?: string;
}

export function ReasoningPanel({ summary, sql }: ReasoningPanelProps) {
  // Extract key points from summary or create defaults
  const points = summary ? summary.split('\n').filter(p => p.trim()) : ['Analysis complete', 'Query generated'];
  const point1 = points[0] || 'Understanding the question and schema';
  const point2 = points[1] || 'Generating and executing the query';

  return (
    <div className="bg-card rounded-lg border border-border p-5 animate-slide-up">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-md bg-primary/10">
          <Brain className="h-4 w-4 text-primary" />
        </div>
        <h3 className="font-semibold text-foreground">Reasoning Trace</h3>
      </div>

      <div className="space-y-3">
        {/* Point 1 */}
        <div className="flex items-start gap-3">
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground flex-shrink-0 mt-0.5">
            <span className="text-xs font-semibold">1</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-foreground/90 leading-relaxed">{point1}</p>
          </div>
        </div>

        {/* Point 2 */}
        <div className="flex items-start gap-3">
          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground flex-shrink-0 mt-0.5">
            <span className="text-xs font-semibold">2</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-foreground/90 leading-relaxed">{point2}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
