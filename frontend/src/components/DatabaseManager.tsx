import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, ChevronDown, Check } from 'lucide-react';
import { listDatabases, selectDatabase, uploadDatabase, DatabaseInfo } from '@/services/api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface DatabaseManagerProps {
  onDatabaseChange?: () => void;
}

export function DatabaseManager({ onDatabaseChange }: DatabaseManagerProps) {
  const [databases, setDatabases] = useState<DatabaseInfo>({ databases: [], current: null });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    try {
      setError(null);
      const dbInfo = await listDatabases();
      setDatabases(dbInfo);
    } catch (err) {
      setError('Failed to load databases');
      console.error(err);
    }
  };

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.db')) {
      setError('Please select a .db file');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await uploadDatabase(file);
      setSuccess(`Database "${result.database}" uploaded successfully`);
      await loadDatabases();
      onDatabaseChange?.();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload database';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const handleSelectDatabase = async (dbName: string) => {
    setIsLoading(true);
    setError(null);

    try {
      await selectDatabase(dbName);
      await loadDatabases();
      onDatabaseChange?.();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to select database';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const currentDbName = databases.current
    ? databases.current === 'default'
      ? 'Default'
      : databases.current.includes('/') 
        ? databases.current.split('/').pop()?.replace('.db', '')
        : databases.current
    : 'No Database';

  return (
    <div className="flex flex-col gap-2">
      {error && (
        <div className="text-xs text-red-500 max-w-xs text-right">{error}</div>
      )}
      {success && (
        <div className="text-xs text-green-500 max-w-xs text-right">{success}</div>
      )}
      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              disabled={isLoading}
              className="gap-2"
            >
              <span className="text-xs truncate max-w-[120px]">{currentDbName}</span>
              <ChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            {databases.databases.length === 0 ? (
              <div className="px-2 py-1.5 text-xs text-muted-foreground">
                No databases available
              </div>
            ) : (
              databases.databases.map((db) => {
                const displayName =
                  db === 'default'
                    ? 'Default'
                    : db.includes('/')
                      ? db.split('/').pop()?.replace('.db', '')
                      : db;
                const isCurrent = databases.current === db;

                return (
                  <DropdownMenuItem
                    key={db}
                    onClick={() => handleSelectDatabase(db)}
                    className="cursor-pointer"
                  >
                    <div className="flex items-center gap-2 w-full">
                      <span className="flex-1">{displayName}</span>
                      {isCurrent && <Check className="h-4 w-4 text-primary" />}
                    </div>
                  </DropdownMenuItem>
                );
              })
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        <label>
          <input
            type="file"
            accept=".db"
            onChange={handleUpload}
            disabled={isLoading}
            className="hidden"
          />
          <Button
            asChild
            variant="ghost"
            size="sm"
            disabled={isLoading}
            className="cursor-pointer gap-2"
          >
            <span>
              <Plus className="h-4 w-4" />
              <span className="text-xs">Add Database</span>
            </span>
          </Button>
        </label>
      </div>
    </div>
  );
}
