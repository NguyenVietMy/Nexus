import express from 'express';
import { checkHealth } from './database';

const app = express();
app.use(express.json());

/**
 * GET /health-check
 * Returns 200 with { status: 'healthy' } when the database is reachable,
 * or 503 with { status: 'unhealthy' } when it is not.
 */
app.get('/health-check', (_req, res) => {
  try {
    const healthy = checkHealth();
    if (healthy) {
      res.status(200).json({ status: 'healthy' });
    } else {
      res.status(503).json({ status: 'unhealthy' });
    }
  } catch {
    res.status(503).json({ status: 'unhealthy' });
  }
});

export default app;
