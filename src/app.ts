import express from 'express';
import { authMiddleware, AuthenticatedRequest } from './middleware/authMiddleware';

const app = express();

app.use(express.json());

app.get('/protected-route', authMiddleware, (req: AuthenticatedRequest, res) => {
  res.status(200).json({ message: 'Access granted', user: req.user });
});

export default app;
