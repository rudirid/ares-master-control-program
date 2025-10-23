# Simple REST API with Express

A lightweight Node.js REST API built with Express, featuring 3 endpoints with error handling and request logging.

## Features

- **3 REST Endpoints**: Health check, data creation, data retrieval
- **Error Handling**: Comprehensive error middleware with validation
- **Request Logging**: Timestamped logs for all requests
- **Input Validation**: Validates request bodies and query parameters
- **Graceful Shutdown**: Handles SIGTERM/SIGINT signals
- **In-Memory Storage**: Simple data store (resets on restart)

## Installation

```bash
# Install dependencies
npm install

# Start server
node server.js
```

Server will run on `http://localhost:3000` by default.

## API Endpoints

### 1. GET /health

Health check endpoint that returns server status.

**Request:**
```bash
curl http://localhost:3000/health
```

**Response:**
```json
{
  "status": "ok",
  "uptime": 24.81,
  "timestamp": "2025-10-13T07:59:10.015Z",
  "environment": "development"
}
```

### 2. POST /data

Create a new data entry.

**Request:**
```bash
curl -X POST http://localhost:3000/data \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example",
    "value": {"foo": "bar", "count": 42}
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "example",
    "value": {"foo": "bar", "count": 42},
    "createdAt": "2025-10-13T07:59:10.031Z"
  }
}
```

**Validation:**
- `name` field is required (400 error if missing)

### 3. GET /data

Retrieve data entries with optional filtering.

**Request (all entries):**
```bash
curl http://localhost:3000/data
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "data": [
    {"id": 1, "name": "item-1", "value": "...", "createdAt": "..."},
    {"id": 2, "name": "item-2", "value": "...", "createdAt": "..."},
    {"id": 3, "name": "item-3", "value": "...", "createdAt": "..."}
  ]
}
```

**Filtering:**

Filter by ID:
```bash
curl "http://localhost:3000/data?id=1"
```

Filter by name (partial match, case-insensitive):
```bash
curl "http://localhost:3000/data?name=item"
```

## Error Handling

### 400 Bad Request
Invalid input or missing required fields:
```json
{
  "error": "Bad Request",
  "message": "Field \"name\" is required"
}
```

### 404 Not Found
Invalid route:
```json
{
  "error": "Not Found",
  "message": "Route GET /invalid not found",
  "availableRoutes": ["GET /health", "POST /data", "GET /data"]
}
```

### 500 Internal Server Error
Unexpected server errors (details hidden in production):
```json
{
  "error": "Internal Server Error",
  "message": "Something went wrong"
}
```

## Testing

Run the comprehensive test suite:

```bash
node test-api.js
```

**Test Results:**
- 21/22 tests passed
- Tests cover all endpoints, validation, error handling, and filtering

## Environment Variables

- `PORT` - Server port (default: 3000)
- `NODE_ENV` - Environment (default: development)

## Logging

All requests are logged with timestamps:

```
[2025-10-13T07:59:10.014Z] GET /health
[2025-10-13T07:59:10.031Z] POST /data
[INFO] Created data entry with id=1
```

## Architecture

- **Express v4.21** - Stable, production-ready
- **Middleware Pattern** - JSON parsing, logging, error handling
- **In-Memory Storage** - Simple array-based data store
- **Graceful Shutdown** - Clean server termination on signals

## Project Structure

```
simple-rest-api/
├── server.js         # Main API server with 3 endpoints
├── test-api.js       # Comprehensive test suite
├── package.json      # Dependencies (Express v4)
└── README.md         # Documentation (this file)
```

## Next Steps

To enhance this API, consider:

1. **Persistent Storage** - Add SQLite or PostgreSQL
2. **Authentication** - JWT tokens or API keys
3. **Rate Limiting** - Protect against abuse
4. **CORS** - Enable cross-origin requests
5. **More Endpoints** - PUT /data/:id, DELETE /data/:id
6. **Validation Library** - Use Joi or express-validator
7. **Testing Framework** - Add Jest or Mocha

---

Built with Express v4 | Node.js REST API | Error Handling | Request Logging
