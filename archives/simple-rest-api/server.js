/**
 * Simple REST API with Express
 *
 * Endpoints:
 * - GET  /health - Health check endpoint
 * - POST /data   - Create/store data
 * - GET  /data   - Retrieve stored data
 *
 * Features:
 * - Error handling middleware
 * - Request logging
 * - Input validation
 * - Graceful shutdown
 */

const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json()); // Parse JSON request bodies

// Simple request logger
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path}`);
  next();
});

// In-memory data store (resets on server restart)
let dataStore = [];
let nextId = 1;

/**
 * GET /health
 * Health check endpoint
 * Returns server status and uptime
 */
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  });
});

/**
 * POST /data
 * Create new data entry
 *
 * Request body:
 * {
 *   "name": "string",
 *   "value": "any"
 * }
 */
app.post('/data', (req, res, next) => {
  try {
    const { name, value } = req.body;

    // Input validation
    if (!name) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Field "name" is required'
      });
    }

    // Create data entry
    const entry = {
      id: nextId++,
      name,
      value,
      createdAt: new Date().toISOString()
    };

    dataStore.push(entry);

    console.log(`[INFO] Created data entry with id=${entry.id}`);

    res.status(201).json({
      success: true,
      data: entry
    });

  } catch (error) {
    next(error); // Pass to error handler
  }
});

/**
 * GET /data
 * Retrieve all data entries
 *
 * Query parameters:
 * - id: Filter by specific ID
 * - name: Filter by name (partial match)
 */
app.get('/data', (req, res, next) => {
  try {
    const { id, name } = req.query;

    let results = dataStore;

    // Filter by ID if provided
    if (id) {
      const numericId = parseInt(id, 10);
      if (isNaN(numericId)) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'Query parameter "id" must be a number'
        });
      }
      results = results.filter(entry => entry.id === numericId);
    }

    // Filter by name if provided (case-insensitive partial match)
    if (name) {
      const searchName = name.toLowerCase();
      results = results.filter(entry =>
        entry.name.toLowerCase().includes(searchName)
      );
    }

    res.status(200).json({
      success: true,
      count: results.length,
      data: results
    });

  } catch (error) {
    next(error); // Pass to error handler
  }
});

/**
 * 404 Handler
 * Catches all undefined routes
 */
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.method} ${req.path} not found`,
    availableRoutes: [
      'GET /health',
      'POST /data',
      'GET /data'
    ]
  });
});

/**
 * Error Handling Middleware
 * Catches all errors and returns consistent error response
 */
app.use((err, req, res, next) => {
  console.error(`[ERROR] ${err.message}`);
  console.error(err.stack);

  // Don't leak error details in production
  const isProduction = process.env.NODE_ENV === 'production';

  res.status(err.status || 500).json({
    error: 'Internal Server Error',
    message: isProduction ? 'Something went wrong' : err.message,
    ...(isProduction ? {} : { stack: err.stack })
  });
});

/**
 * Start server
 */
const server = app.listen(PORT, () => {
  console.log('='.repeat(50));
  console.log('Simple REST API Server');
  console.log('='.repeat(50));
  console.log(`[OK] Server running on http://localhost:${PORT}`);
  console.log(`[OK] Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log('\nAvailable endpoints:');
  console.log(`  GET  http://localhost:${PORT}/health`);
  console.log(`  POST http://localhost:${PORT}/data`);
  console.log(`  GET  http://localhost:${PORT}/data`);
  console.log('\nPress Ctrl+C to stop\n');
});

/**
 * Graceful shutdown
 */
process.on('SIGTERM', () => {
  console.log('\n[INFO] SIGTERM received, shutting down gracefully...');
  server.close(() => {
    console.log('[OK] Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\n[INFO] SIGINT received, shutting down gracefully...');
  server.close(() => {
    console.log('[OK] Server closed');
    process.exit(0);
  });
});
