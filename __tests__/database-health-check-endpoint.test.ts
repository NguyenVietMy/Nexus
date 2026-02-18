const request = require('supertest');
const app = require('../app'); // assuming Express app is exported from app.js

// Mocking the database connection
jest.mock('../database', () => ({
  isConnected: jest.fn(),
}));

const { isConnected } = require('../database');

describe('Database Health Check Endpoint', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should return 200 status for a healthy connection', async () => {
    isConnected.mockReturnValue(true);

    const response = await request(app).get('/health/db');
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ status: 'healthy' });
  });

  test('should return an error for a database downtime', async () => {
    isConnected.mockReturnValue(false);

    const response = await request(app).get('/health/db');
    expect(response.status).toBe(503);
    expect(response.body).toEqual({ status: 'unhealthy', error: 'Database unavailable' });
  });

  test('should respond within acceptable time under normal conditions', async () => {
    isConnected.mockReturnValue(true);

    const start = Date.now();
    const response = await request(app).get('/health/db');
    const duration = Date.now() - start;

    expect(response.status).toBe(200);
    expect(duration).toBeLessThan(100); // ensure response time is under 100ms
  });

  test('should handle response time under stress conditions', async () => {
    isConnected.mockReturnValue(true);

    const requests = Array.from({ length: 100 }, () => request(app).get('/health/db'));
    const start = Date.now();
    await Promise.all(requests);
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(5000); // ensure all requests complete under 5s
  });
});