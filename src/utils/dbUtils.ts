let _dbDown = false;

/**
 * Returns true when the database is available (i.e. not simulating downtime).
 */
export function isDatabaseHealthy(): boolean {
  return !_dbDown;
}

/**
 * Simulates a database connectivity failure for testing purposes.
 */
export async function simulateDatabaseDowntime(): Promise<void> {
  _dbDown = true;
}

/**
 * Resets the database simulation state back to healthy.
 */
export async function resetDatabase(): Promise<void> {
  _dbDown = false;
}
