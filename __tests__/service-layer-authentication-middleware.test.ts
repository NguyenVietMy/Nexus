import request from 'supertest';
import app from '../src/app'; // Assuming Express app is exported from this file
import { createToken, expireToken } from '../src/utils/tokenUtil';

// Mock user data
const userWithPermissions = {
  id: 'user1',
  permissions: ['read', 'write']
};

const userWithoutPermissions = {
  id: 'user2',
  permissions: []
};

// Generate tokens
const validToken = createToken(userWithPermissions);
const expiredToken = createToken(userWithPermissions, { expiresIn: '-1h' }); // Token already expired

// Test suite

describe('Service Layer Authentication Middleware', () => {
  test('should deny service calls without authentication', async () => {
    const res = await request(app).get('/protected-route');
    expect(res.statusCode).toBe(401);
    expect(res.body.message).toBe('Unauthorized');
  });

  test('should allow authenticated requests with correct permissions', async () => {
    const res = await request(app)
      .get('/protected-route')
      .set('Authorization', `Bearer ${validToken}`);
    expect(res.statusCode).toBe(200);
    expect(res.body.message).toBe('Access granted');
  });

  test('should deny requests with expired tokens', async () => {
    const res = await request(app)
      .get('/protected-route')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect(res.statusCode).toBe(401);
    expect(res.body.message).toBe('Token expired');
  });

  test('should refresh token when expired', async () => {
    // Assume refreshToken function exists and works correctly
    const refreshToken = jest.fn().mockReturnValue(createToken(userWithPermissions));

    // Simulate token expiration and refresh
    const res = await request(app)
      .get('/protected-route')
      .set('Authorization', `Bearer ${expiredToken}`)
      .set('x-refresh-token', refreshToken);

    expect(refreshToken).toHaveBeenCalled();
    expect(res.statusCode).toBe(200);
    expect(res.body.message).toBe('Token refreshed');
  });

});
