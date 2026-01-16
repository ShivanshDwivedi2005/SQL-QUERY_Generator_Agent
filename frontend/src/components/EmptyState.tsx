import { Database, Sparkles, ArrowRight, Code, Brain, Shield } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full py-12 animate-fade-in">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-primary/10 rounded-full blur-2xl" />
        <div className="relative w-20 h-20 rounded-2xl bg-secondary border border-primary/20 flex items-center justify-center">
          <Database className="h-10 w-10 text-primary" />
        </div>
      </div>

      <h2 className="text-xl font-semibold text-foreground mb-2">
        Ask your database anything
      </h2>
      <p className="text-muted-foreground text-center max-w-md mb-8">
        Type a question in natural language and watch the system reason through
        your query step by step.
      </p>

      <div className="grid gap-4 max-w-lg w-full">
        <FeatureCard
          icon={Brain}
          title="Intelligent Reasoning"
          description="See how the system interprets your intent and chooses the right strategy"
        />
        <FeatureCard
          icon={Code}
          title="Transparent SQL"
          description="Review the generated query before it runs — no black boxes"
        />
        <FeatureCard
          icon={Shield}
          title="Safe & Read-Only"
          description="All queries are read-only, protecting your data integrity"
        />
      </div>
    </div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Brain;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-4 p-4 rounded-lg bg-secondary/50 border border-border/50 hover:border-primary/30 transition-colors">
      <div className="p-2 rounded-md bg-primary/10 shrink-0">
        <Icon className="h-5 w-5 text-primary" />
      </div>
      <div>
        <h3 className="font-medium text-foreground mb-0.5">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
