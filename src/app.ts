import express, { Request, Response } from 'express';
import { isDatabaseHealthy } from './utils/dbUtils';

const app = express();

app.use(express.json());

app.get('/health/db', (_req: Request, res: Response) => {
  if (isDatabaseHealthy()) {
    res.status(200).json({ status: 'healthy' });
  } else {
    res.status(503).json({ status: 'unhealthy' });
  }
});

export default app;
