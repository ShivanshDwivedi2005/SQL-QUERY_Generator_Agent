import { QueryResponse, ExampleQuery } from '@/types/query';

export const exampleQueries: ExampleQuery[] = [
  { label: 'Top selling tracks', query: 'Which tracks have sold the most?', category: 'simple' },
  { label: 'Revenue by country', query: 'Total revenue by country, sorted highest first', category: 'moderate' },
  { label: 'Inactive customers', query: 'Which customers have never made a purchase?', category: 'reasoning' },
  { label: 'Best employees', query: 'Who are the best performing employees?', category: 'ambiguous' },
  { label: 'Show tables', query: 'What tables exist in this database?', category: 'meta' },
];

export const mockResponses: Record<string, QueryResponse> = {
  'Which tracks have sold the most?': {
    reasoning: [
      { id: '1', label: 'Intent Analysis', detail: 'User wants to find tracks ranked by sales volume', status: 'complete' },
      { id: '2', label: 'Schema Discovery', detail: 'Found Track, InvoiceLine tables with quantity data', status: 'complete' },
      { id: '3', label: 'Strategy Selection', detail: 'Using JOIN with GROUP BY and ORDER BY DESC for ranking', status: 'complete' },
      { id: '4', label: 'Query Optimization', detail: 'Added LIMIT 10 for performance; indexed columns used', status: 'complete' },
    ],
    sql: `SELECT 
  t.Name AS track_name,
  ar.Name AS artist,
  SUM(il.Quantity) AS total_sold
FROM Track t
JOIN Album al ON t.AlbumId = al.AlbumId
JOIN Artist ar ON al.ArtistId = ar.ArtistId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY t.TrackId, t.Name, ar.Name
ORDER BY total_sold DESC
LIMIT 10;`,
    result: {
      columns: ['track_name', 'artist', 'total_sold'],
      rows: [
        { track_name: 'The Trooper', artist: 'Iron Maiden', total_sold: 5 },
        { track_name: 'Hallowed Be Thy Name', artist: 'Iron Maiden', total_sold: 4 },
        { track_name: 'Balls to the Wall', artist: 'Accept', total_sold: 4 },
        { track_name: 'Inject The Venom', artist: 'AC/DC', total_sold: 3 },
        { track_name: 'Evil Walks', artist: 'AC/DC', total_sold: 3 },
      ],
    },
    summary: 'The Trooper by Iron Maiden is the best-selling track with 5 units sold, followed by Hallowed Be Thy Name and Balls to the Wall.',
    status: 'success',
  },
  'Total revenue by country, sorted highest first': {
    reasoning: [
      { id: '1', label: 'Intent Analysis', detail: 'User wants aggregated revenue grouped by billing country', status: 'complete' },
      { id: '2', label: 'Schema Discovery', detail: 'Invoice table contains BillingCountry and Total columns', status: 'complete' },
      { id: '3', label: 'Strategy Selection', detail: 'Simple GROUP BY on BillingCountry with SUM(Total)', status: 'complete' },
      { id: '4', label: 'Formatting', detail: 'Added currency formatting and descending sort', status: 'complete' },
    ],
    sql: `SELECT 
  BillingCountry AS country,
  ROUND(SUM(Total), 2) AS total_revenue,
  COUNT(*) AS order_count
FROM Invoice
GROUP BY BillingCountry
ORDER BY total_revenue DESC;`,
    result: {
      columns: ['country', 'total_revenue', 'order_count'],
      rows: [
        { country: 'USA', total_revenue: 523.06, order_count: 91 },
        { country: 'Canada', total_revenue: 303.96, order_count: 56 },
        { country: 'France', total_revenue: 195.10, order_count: 35 },
        { country: 'Brazil', total_revenue: 190.10, order_count: 35 },
        { country: 'Germany', total_revenue: 156.48, order_count: 28 },
        { country: 'United Kingdom', total_revenue: 112.86, order_count: 21 },
      ],
    },
    summary: 'USA leads with $523.06 in revenue from 91 orders, followed by Canada ($303.96) and France ($195.10).',
    status: 'success',
  },
  'Which customers have never made a purchase?': {
    reasoning: [
      { id: '1', label: 'Intent Analysis', detail: 'Finding customers with zero invoices — requires anti-join pattern', status: 'complete' },
      { id: '2', label: 'Schema Discovery', detail: 'Customer table links to Invoice via CustomerId foreign key', status: 'complete' },
      { id: '3', label: 'Strategy Selection', detail: 'Using LEFT JOIN with NULL check (more efficient than NOT IN for large datasets)', status: 'complete' },
      { id: '4', label: 'Validation', detail: 'Verified referential integrity; all customers have valid IDs', status: 'complete' },
    ],
    sql: `SELECT 
  c.CustomerId,
  c.FirstName || ' ' || c.LastName AS customer_name,
  c.Email,
  c.Country
FROM Customer c
LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE i.InvoiceId IS NULL;`,
    result: {
      columns: ['CustomerId', 'customer_name', 'Email', 'Country'],
      rows: [],
    },
    summary: 'All customers in the database have made at least one purchase. There are no inactive customers.',
    status: 'empty',
  },
  'Who are the best performing employees?': {
    reasoning: [
      { id: '1', label: 'Intent Analysis', detail: 'Ambiguous query — "best performing" needs clarification', status: 'complete' },
      { id: '2', label: 'Assumption Made', detail: 'Interpreting as employees with highest sales support revenue', status: 'complete' },
    ],
    sql: '',
    result: { columns: [], rows: [] },
    summary: '',
    status: 'ambiguous',
    clarification: 'What does "best performing" mean to you? I can measure by:\n• Total revenue from supported customers\n• Number of customers supported\n• Average order value per customer\n• Customer retention rate',
  },
  'What tables exist in this database?': {
    reasoning: [
      { id: '1', label: 'Intent Analysis', detail: 'Meta-query requesting schema introspection', status: 'complete' },
      { id: '2', label: 'Strategy Selection', detail: 'Querying SQLite system catalog (sqlite_master)', status: 'complete' },
    ],
    sql: `SELECT name, type 
FROM sqlite_master 
WHERE type = 'table' 
ORDER BY name;`,
    result: {
      columns: ['name', 'type'],
      rows: [
        { name: 'Album', type: 'table' },
        { name: 'Artist', type: 'table' },
        { name: 'Customer', type: 'table' },
        { name: 'Employee', type: 'table' },
        { name: 'Genre', type: 'table' },
        { name: 'Invoice', type: 'table' },
        { name: 'InvoiceLine', type: 'table' },
        { name: 'MediaType', type: 'table' },
        { name: 'Playlist', type: 'table' },
        { name: 'PlaylistTrack', type: 'table' },
        { name: 'Track', type: 'table' },
      ],
    },
    summary: 'The Chinook database contains 11 tables covering music catalog (Album, Artist, Track, Genre), sales (Invoice, InvoiceLine, Customer), and organization (Employee, Playlist).',
    status: 'success',
  },
};

export const getDefaultResponse = (): QueryResponse => ({
  reasoning: [
    { id: '1', label: 'Intent Analysis', detail: 'Parsing natural language query for database intent', status: 'complete' },
    { id: '2', label: 'Schema Discovery', detail: 'Exploring relevant tables and relationships', status: 'complete' },
    { id: '3', label: 'Strategy Selection', detail: 'Choosing optimal query pattern', status: 'complete' },
    { id: '4', label: 'Query Generation', detail: 'Building safe, read-only SQL statement', status: 'complete' },
  ],
  sql: `-- Generated SQL based on your question
SELECT * FROM table LIMIT 10;`,
  result: {
    columns: ['id', 'name', 'value'],
    rows: [
      { id: 1, name: 'Example', value: 100 },
    ],
  },
  summary: 'Query executed successfully with sample results.',
  status: 'success',
});
