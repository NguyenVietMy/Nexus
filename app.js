const express = require('express');
const { isConnected } = require('./database');

const app = express();

app.use(express.json());

/**
 * GET /health/db
 * Returns database connectivity status.
 * 200 { status: 'healthy' } when connected.
 * 503 { status: 'unhealthy', error: 'Database unavailable' } when not connected.
 */
app.get('/health/db', (req, res) => {
  if (isConnected()) {
    return res.status(200).json({ status: 'healthy' });
  }
  return res.status(503).json({ status: 'unhealthy', error: 'Database unavailable' });
});

module.exports = app;
