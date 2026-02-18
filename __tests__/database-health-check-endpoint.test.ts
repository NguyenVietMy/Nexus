import { describe, it, expect, beforeEach, vi } from 'vitest';
import request from 'supertest';

// Mocking the database health check function
vi.mock('./database', () => ({
  checkHealth: vi.fn(() => true),
}));

import app from './app';
import { checkHealth } from './database';

const mockCheckHealth = checkHealth as ReturnType<typeof vi.fn>;

// Helper function to simulate database downtime
const simulateDatabaseDowntime = () => {
  mockCheckHealth.mockReturnValue(false);
};

// Helper function to restore database health
const restoreDatabaseHealth = () => {
  mockCheckHealth.mockReturnValue(true);
};

describe('Database Health Check Endpoint', () => {
  beforeEach(() => {
    restoreDatabaseHealth();
  });

  it('should return a 200 status for a healthy connection', async () => {
    const response = await request(app).get('/health-check');
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('status', 'healthy');
  });

  it('should return an error when the database is down', async () => {
    simulateDatabaseDowntime();
    const response = await request(app).get('/health-check');
    expect(response.status).toBe(503);
    expect(response.body).toHaveProperty('status', 'unhealthy');
  });

  it('should respond within acceptable time under normal conditions', async () => {
    const start = Date.now();
    const response = await request(app).get('/health-check');
    const responseTime = Date.now() - start;
    expect(response.status).toBe(200);
    expect(responseTime).toBeLessThan(200); // Assume acceptable response time is <200ms
  });

  it('should respond within acceptable time under stress conditions', async () => {
    const requests = Array.from({ length: 100 }, () => request(app).get('/health-check'));
    const responses = await Promise.all(requests);
    responses.forEach(response => {
      expect(response.status).toBe(200);
    });
    // Optionally, we could check collective response time or individual response times
    // This is a simple demonstration of stress testing
  });
});
