import jwt from 'jsonwebtoken';

const JWT_SECRET = 'pee-auth-secret-key-for-testing';

export interface UserPayload {
  id: string;
  permissions: string[];
}

export interface TokenOptions {
  expiresIn?: string;
}

export function createToken(user: UserPayload, options?: TokenOptions): string {
  const expiresIn = options?.expiresIn || '1h';
  return jwt.sign(
    { id: user.id, permissions: user.permissions },
    JWT_SECRET,
    { expiresIn }
  );
}

export function expireToken(token: string): boolean {
  try {
    jwt.verify(token, JWT_SECRET);
    return false;
  } catch {
    return true;
  }
}

export { JWT_SECRET };
