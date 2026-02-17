import request from 'supertest';
import app from '../app'; // Assuming Express app is exported from app.js
import { generateToken, refreshToken } from '../auth'; // Assuming these functions exist

let validToken;
let expiredToken;
let refreshTokenValue;

beforeAll(() => {
  // Simulating token generation
  validToken = generateToken({ userId: 1, permissions: ['read', 'write'] }, '1h');
  expiredToken = generateToken({ userId: 1, permissions: ['read', 'write'] }, '-1h');
  refreshTokenValue = refreshToken({ userId: 1 });
});

describe('Service Layer Authentication Middleware', () => {
  test('should deny access for calls without authentication', async () => {
    const response = await request(app).get('/protected-route');
    expect(response.status).toBe(401);
    expect(response.body.message).toBe('Unauthorized');
  });

  test('should allow access for authenticated requests with correct permissions', async () => {
    const response = await request(app)
      .get('/protected-route')
      .set('Authorization', `Bearer ${validToken}`);
    expect(response.status).toBe(200);
    expect(response.body.message).toBe('Access granted');
  });

  test('should deny access for expired tokens', async () => {
    const response = await request(app)
      .get('/protected-route')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect(response.status).toBe(401);
    expect(response.body.message).toBe('Token expired');
  });

  test('should refresh token and allow access', async () => {
    const refreshResponse = await request(app)
      .post('/auth/refresh')
      .send({ token: refreshTokenValue });
    expect(refreshResponse.status).toBe(200);
    const newToken = refreshResponse.body.token;
    const accessResponse = await request(app)
      .get('/protected-route')
      .set('Authorization', `Bearer ${newToken}`);
    expect(accessResponse.status).toBe(200);
    expect(accessResponse.body.message).toBe('Access granted');
  });
});