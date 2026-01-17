import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, ChevronDown, Check, Upload, Database, Eye } from 'lucide-react';
import { listDatabases, selectDatabase, uploadDatabase, viewDatabase, DatabaseInfo, DatabaseView } from '@/services/api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

interface DatabaseManagerProps {
  onDatabaseChange?: () => void;
}

export function DatabaseManager({ onDatabaseChange }: DatabaseManagerProps) {
  const [databases, setDatabases] = useState<DatabaseInfo>({ databases: [], current: null });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [databaseView, setDatabaseView] = useState<DatabaseView | null>(null);
  const [isLoadingView, setIsLoadingView] = useState(false);

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
      setError('Please select a SQLite database file (.db)');
      setTimeout(() => setError(null), 3000);
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await uploadDatabase(file);
      setSuccess(result.message || `Database "${result.database}" uploaded successfully`);
      await loadDatabases();
      onDatabaseChange?.();
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload database';
      setError(errorMessage);
      setTimeout(() => setError(null), 5000);
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

  const handleViewDatabase = async () => {
    if (!databases.current) {
      setError('No database selected');
      setTimeout(() => setError(null), 3000);
      return;
    }

    setIsLoadingView(true);
    setIsViewDialogOpen(true);

    try {
      const view = await viewDatabase();
      setDatabaseView(view);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to view database';
      setError(errorMessage);
      setTimeout(() => setError(null), 5000);
      setIsViewDialogOpen(false);
    } finally {
      setIsLoadingView(false);
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
        <div className="text-xs text-red-500 max-w-xs text-right animate-in fade-in">
          {error}
        </div>
      )}
      {success && (
        <div className="text-xs text-green-500 max-w-xs text-right animate-in fade-in">
          {success}
        </div>
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
              <Database className="h-4 w-4" />
              <span className="text-xs truncate max-w-[120px]">{currentDbName}</span>
              <ChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            {databases.databases.length === 0 ? (
              <div className="px-2 py-1.5 text-xs text-muted-foreground">
                No databases available
              </div>
            ) : (
              databases.databases.map((db) => {
                const displayName =
                  db === 'default'
                    ? 'Default Database'
                    : db;
                const isCurrent = databases.current === db;

                return (
                  <DropdownMenuItem
                    key={db}
                    onClick={() => handleSelectDatabase(db)}
                    className="cursor-pointer"
                  >
                    <div className="flex items-center gap-2 w-full">
                      <Database className="h-4 w-4 text-muted-foreground" />
                      <span className="flex-1 truncate">{displayName}</span>
                      {isCurrent && <Check className="h-4 w-4 text-primary" />}
                    </div>
                  </DropdownMenuItem>
                );
              })
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="outline"
          size="sm"
          disabled={isLoading || !databases.current}
          className="gap-2"
          onClick={handleViewDatabase}
        >
          <Eye className="h-4 w-4" />
          <span className="text-xs">View Database</span>
        </Button>

        <div className="relative">
          <input
            id="database-upload"
            type="file"
            accept=".db"
            onChange={handleUpload}
            disabled={isLoading}
            className="hidden"
          />
          <Button
            variant="default"
            size="sm"
            disabled={isLoading}
            className="gap-2"
            onClick={() => document.getElementById('database-upload')?.click()}
          >
            <Upload className="h-4 w-4" />
            <span className="text-xs">Upload Database</span>
          </Button>
        </div>
      </div>

      {/* View Database Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Database Structure</DialogTitle>
            <DialogDescription>
              {databaseView ? `Database: ${databaseView.database}` : 'Loading database information...'}
            </DialogDescription>
          </DialogHeader>

          {isLoadingView ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : databaseView ? (
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">
                {databaseView.tables.length} table{databaseView.tables.length !== 1 ? 's' : ''} found
              </div>

              <Accordion type="single" collapsible className="w-full">
                {databaseView.tables.map((table) => (
                  <AccordionItem key={table.name} value={table.name}>
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center gap-2 text-left">
                        <Database className="h-4 w-4 text-primary" />
                        <div>
                          <div className="font-semibold">{table.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {table.row_count} row{table.row_count !== 1 ? 's' : ''} • {table.columns.length} column{table.columns.length !== 1 ? 's' : ''}
                          </div>
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-4 pt-2">
                        {/* Columns Schema */}
                        <div>
                          <h4 className="text-sm font-semibold mb-2">Columns</h4>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Name</TableHead>
                                <TableHead>Type</TableHead>
                                <TableHead>Constraints</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {table.columns.map((column) => (
                                <TableRow key={column.name}>
                                  <TableCell className="font-mono text-xs">
                                    {column.name}
                                    {column.pk && <span className="ml-2 text-xs text-amber-500">(PK)</span>}
                                  </TableCell>
                                  <TableCell className="text-xs text-muted-foreground">{column.type}</TableCell>
                                  <TableCell className="text-xs">
                                    {column.notnull && <span className="text-red-500">NOT NULL</span>}
                                    {column.default_value && <span className="ml-2 text-blue-500">DEFAULT: {column.default_value}</span>}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>

                        {/* Sample Data */}
                        {table.sample_data.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold mb-2">Sample Data (First 5 rows)</h4>
                            <div className="border rounded-lg overflow-hidden">
                              <div className="max-h-60 overflow-auto">
                                <Table>
                                  <TableHeader className="sticky top-0 bg-secondary">
                                    <TableRow>
                                      {table.columns.map((col) => (
                                        <TableHead key={col.name} className="text-xs">{col.name}</TableHead>
                                      ))}
                                    </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                    {table.sample_data.map((row, idx) => (
                                      <TableRow key={idx}>
                                        {table.columns.map((col) => (
                                          <TableCell key={col.name} className="text-xs">
                                            {row[col.name] !== null && row[col.name] !== undefined
                                              ? String(row[col.name])
                                              : <span className="text-muted-foreground italic">NULL</span>}
                                          </TableCell>
                                        ))}
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
