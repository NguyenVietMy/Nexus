import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { JWT_SECRET, UserPayload, createToken } from '../utils/tokenUtil';

export interface AuthenticatedRequest extends Request {
  user?: UserPayload;
}

export function authMiddleware(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
): void {
  const authHeader = req.headers.authorization;
  const refreshTokenHeader = req.headers['x-refresh-token'];

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({ message: 'Unauthorized' });
    return;
  }

  const token = authHeader.split(' ')[1];

  try {
    const decoded = jwt.verify(token, JWT_SECRET) as UserPayload;
    req.user = decoded;
    next();
  } catch (err: any) {
    if (err.name === 'TokenExpiredError' && refreshTokenHeader) {
      // Token is expired but a refresh token header is present — issue a new token
      const decoded = jwt.decode(token) as UserPayload | null;
      if (decoded) {
        const newToken = createToken({ id: decoded.id, permissions: decoded.permissions });
        res.status(200).json({ message: 'Token refreshed', token: newToken });
        return;
      }
    }

    if (err.name === 'TokenExpiredError') {
      res.status(401).json({ message: 'Token expired' });
      return;
    }

    res.status(401).json({ message: 'Unauthorized' });
  }
}
