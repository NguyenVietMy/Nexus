import request from 'supertest';
import app from '../src/app'; // Assuming the Express app is exported from this file
import { simulateDatabaseDowntime, resetDatabase } from '../src/utils/dbUtils';

describe('Database Health Check Endpoint', () => {
  afterAll(async () => {
    // Ensure the database is reset after tests
    await resetDatabase();
  });

  test('returns 200 for a healthy connection', async () => {
    const response = await request(app).get('/health/db');
    expect(response.status).toBe(200);
    expect(response.body.status).toBe('healthy');
  });

  test('returns an error during database downtime', async () => {
    await simulateDatabaseDowntime();

    const response = await request(app).get('/health/db');
    expect(response.status).not.toBe(200);
    expect(response.body.status).toBe('unhealthy');

    await resetDatabase(); // Reset database for other tests
  });

  test('response time under normal conditions', async () => {
    const start = Date.now();
    const response = await request(app).get('/health/db');
    const duration = Date.now() - start;

    expect(response.status).toBe(200);
    expect(duration).toBeLessThan(200); // Assuming 200ms is the acceptable threshold
  });

  test('response time under stressed conditions', async () => {
    const requests = Array.from({ length: 100 }, () => request(app).get('/health/db'));

    const start = Date.now();
    await Promise.all(requests);
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(5000); // Assuming 5000ms is the acceptable threshold under stress
  });
});
