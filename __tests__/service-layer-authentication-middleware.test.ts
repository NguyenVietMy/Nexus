import request from 'supertest';
import app from '../app'; // Assuming app is your Express application
import jwt from 'jsonwebtoken';

// Mock data
const validToken = jwt.sign({ userId: 1, permissions: ['read', 'write'] }, 'secret', { expiresIn: '1h' });
const expiredToken = jwt.sign({ userId: 1, permissions: ['read', 'write'] }, 'secret', { expiresIn: '-1h' });
const refreshToken = jwt.sign({ userId: 1 }, 'secret', { expiresIn: '7d' });

// Middleware mock for token refresh
jest.mock('../middleware/tokenRefresh', () => (req, res, next) => {
  if (req.headers['x-refresh-token'] === refreshToken) {
    req.newToken = validToken;
  }
  next();
});

describe('Service Layer Authentication Middleware', () => {
  test('should deny access to unauthenticated requests', async () => {
    const response = await request(app)
      .get('/protected-route')
      .send();

    expect(response.status).toBe(401);
    expect(response.body.message).toBe('Unauthorized');
  });

  test('should allow access to authenticated requests with correct permissions', async () => {
    const response = await request(app)
      .get('/protected-route')
      .set('Authorization', `Bearer ${validToken}`)
      .send();

    expect(response.status).toBe(200);
    expect(response.body.message).toBe('Access granted');
  });

  test('should handle token expiration and refresh', async () => {
    const response = await request(app)
      .get('/protected-route')
      .set('Authorization', `Bearer ${expiredToken}`)
      .set('x-refresh-token', refreshToken)
      .send();

    expect(response.status).toBe(200);
    expect(response.body.message).toBe('Token refreshed');
    expect(response.body.token).toBeDefined();
    const decoded = jwt.verify(response.body.token, 'secret');
    expect(decoded.userId).toBe(1);
  });
});