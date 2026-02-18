/**
 * Database module — provides health check for the database connection.
 * In production this would run a real query (e.g. SELECT 1).
 */
export function checkHealth(): boolean {
  return true;
}
