import { ChangeEvent, useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Database, Eye, RefreshCw, Upload, XCircle } from 'lucide-react';
import {
  fetchConnectionStatus,
  MAX_UPLOAD_SIZE_BYTES,
  uploadData,
  viewDatabase,
  DatabaseInfo,
  DatabaseView,
} from '@/services/api';
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

export function DatabaseManager() {
  const [databaseInfo, setDatabaseInfo] = useState<DatabaseInfo>({
    databases: [],
    current: null,
    provider: 'neon',
    connected: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [databaseView, setDatabaseView] = useState<DatabaseView | null>(null);
  const [isLoadingView, setIsLoadingView] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const loadDatabaseInfo = useCallback(async () => {
    setIsLoading(true);
    try {
      setError(null);
      setSuccess(null);
      const info = await fetchConnectionStatus();
      setDatabaseInfo(info);
    } catch (err) {
      setError('Failed to load database connection');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDatabaseInfo();
  }, [loadDatabaseInfo]);

  const handleViewDatabase = async () => {
    let isConnected = databaseInfo.connected;
    if (!isConnected) {
      const refreshed = await fetchConnectionStatus();
      setDatabaseInfo(refreshed);
      isConnected = refreshed.connected;
    }
    if (!isConnected) {
      setError('No Neon database connected');
      setTimeout(() => setError(null), 3000);
      return;
    }

    setIsLoadingView(true);
    setIsViewDialogOpen(true);

    try {
      setError(null);
      setSuccess(null);
      const view = await viewDatabase();
      setDatabaseView(view);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to view database';
      setError(message);
      setIsViewDialogOpen(false);
    } finally {
      setIsLoadingView(false);
    }
  };

  const handleUploadData = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    let isConnected = databaseInfo.connected;
    if (!isConnected) {
      const refreshed = await fetchConnectionStatus();
      setDatabaseInfo(refreshed);
      isConnected = refreshed.connected;
    }
    if (!isConnected) {
      setError('Connect Neon database before uploading data');
      setTimeout(() => setError(null), 4000);
      return;
    }

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Only CSV files are supported');
      setTimeout(() => setError(null), 4000);
      return;
    }

    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      setError('Data size is larger than 5 MB');
      setTimeout(() => setError(null), 4000);
      return;
    }

    setIsUploading(true);
    try {
      setError(null);
      setSuccess(null);
      const result = await uploadData(file);
      if (!result.success) {
        setError(result.error || 'Failed to upload data');
        setTimeout(() => setError(null), 5000);
        return;
      }

      await loadDatabaseInfo();
      setDatabaseView(null);
      setSuccess(result.message || 'Data uploaded successfully');
      setTimeout(() => setSuccess(null), 5000);
    } finally {
      setIsUploading(false);
    }
  };

  const currentDbName = databaseInfo.current || 'Not Connected';

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
        <div className="h-9 px-3 rounded-md border border-border bg-secondary flex items-center gap-2">
          <Database className="h-4 w-4 text-muted-foreground" />
          <span className="text-xs truncate max-w-[150px]">{currentDbName}</span>
          {databaseInfo.connected ? (
            <CheckCircle2 className="h-4 w-4 text-primary" />
          ) : (
            <XCircle className="h-4 w-4 text-destructive" />
          )}
        </div>

        <Button
          variant="outline"
          size="sm"
          disabled={isLoading}
          className="gap-2"
          onClick={loadDatabaseInfo}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span className="text-xs">Refresh</span>
        </Button>

        <Button
          variant="outline"
          size="sm"
          disabled={isLoadingView || !databaseInfo.connected}
          className="gap-2"
          onClick={handleViewDatabase}
        >
          <Eye className="h-4 w-4" />
          <span className="text-xs">View Database</span>
        </Button>

        <input
          id="data-upload"
          type="file"
          accept=".csv,text/csv"
          onChange={handleUploadData}
          disabled={isUploading}
          className="hidden"
        />
        <Button
          variant="default"
          size="sm"
          disabled={isUploading}
          className="gap-2"
          onClick={() => document.getElementById('data-upload')?.click()}
        >
          <Upload className={`h-4 w-4 ${isUploading ? 'animate-pulse' : ''}`} />
          <span className="text-xs">{isUploading ? 'Uploading...' : 'Upload Data'}</span>
        </Button>
      </div>

      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Neon Database Structure</DialogTitle>
            <DialogDescription>
              {databaseView ? `Database: ${databaseView.database}` : 'Loading database information...'}
            </DialogDescription>
          </DialogHeader>

          {isLoadingView ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
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

                        {table.sample_data.length > 0 && (
                          <div>
                            <h4 className="text-sm font-semibold mb-2">Sample Data</h4>
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
