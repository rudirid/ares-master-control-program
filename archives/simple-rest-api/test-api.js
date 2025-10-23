/**
 * Simple API Test Script
 * Tests all endpoints and verifies functionality
 */

const http = require('http');

const BASE_URL = 'http://localhost:3000';
let testsPassed = 0;
let testsFailed = 0;

// Helper function to make HTTP requests
function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = http.request(url, options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          const jsonBody = body ? JSON.parse(body) : null;
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: jsonBody
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: body
          });
        }
      });
    });

    req.on('error', reject);

    if (data) {
      req.write(JSON.stringify(data));
    }

    req.end();
  });
}

// Test assertion helper
function assert(condition, testName) {
  if (condition) {
    console.log(`[OK] ${testName}`);
    testsPassed++;
  } else {
    console.log(`[X] ${testName}`);
    testsFailed++;
  }
}

// Run all tests
async function runTests() {
  console.log('='.repeat(60));
  console.log('TESTING REST API');
  console.log('='.repeat(60));
  console.log('');

  try {
    // Test 1: GET /health
    console.log('Test 1: GET /health');
    const healthRes = await makeRequest('GET', '/health');
    assert(healthRes.status === 200, 'Health endpoint returns 200');
    assert(healthRes.body.status === 'ok', 'Health status is "ok"');
    assert(typeof healthRes.body.uptime === 'number', 'Health includes uptime');
    console.log(`  Response: ${JSON.stringify(healthRes.body)}`);
    console.log('');

    // Test 2: POST /data (valid)
    console.log('Test 2: POST /data (valid data)');
    const createRes = await makeRequest('POST', '/data', {
      name: 'test-item',
      value: { foo: 'bar', count: 42 }
    });
    assert(createRes.status === 201, 'POST /data returns 201');
    assert(createRes.body.success === true, 'Response has success=true');
    assert(createRes.body.data.id === 1, 'First entry has id=1');
    assert(createRes.body.data.name === 'test-item', 'Name is stored correctly');
    console.log(`  Response: ${JSON.stringify(createRes.body)}`);
    console.log('');

    // Test 3: POST /data (invalid - missing name)
    console.log('Test 3: POST /data (invalid - missing name)');
    const createInvalidRes = await makeRequest('POST', '/data', {
      value: 'no-name-field'
    });
    assert(createInvalidRes.status === 400, 'POST /data with missing name returns 400');
    assert(createInvalidRes.body.error === 'Bad Request', 'Error message is "Bad Request"');
    console.log(`  Response: ${JSON.stringify(createInvalidRes.body)}`);
    console.log('');

    // Test 4: POST /data (create multiple entries)
    console.log('Test 4: POST /data (create multiple entries)');
    await makeRequest('POST', '/data', { name: 'item-2', value: 'second' });
    await makeRequest('POST', '/data', { name: 'item-3', value: 'third' });
    console.log('  [OK] Created 2 additional entries');
    console.log('');

    // Test 5: GET /data (retrieve all)
    console.log('Test 5: GET /data (retrieve all)');
    const getAllRes = await makeRequest('GET', '/data');
    assert(getAllRes.status === 200, 'GET /data returns 200');
    assert(getAllRes.body.success === true, 'Response has success=true');
    assert(getAllRes.body.count === 3, 'Data store contains 3 entries');
    assert(Array.isArray(getAllRes.body.data), 'Data is an array');
    console.log(`  Response: count=${getAllRes.body.count}, entries=${getAllRes.body.data.length}`);
    console.log('');

    // Test 6: GET /data?id=1 (filter by ID)
    console.log('Test 6: GET /data?id=1 (filter by ID)');
    const getByIdRes = await makeRequest('GET', '/data?id=1');
    assert(getByIdRes.status === 200, 'GET /data?id=1 returns 200');
    assert(getByIdRes.body.count === 1, 'Filtered result has 1 entry');
    assert(getByIdRes.body.data[0].id === 1, 'Entry has correct ID');
    console.log(`  Response: ${JSON.stringify(getByIdRes.body.data[0])}`);
    console.log('');

    // Test 7: GET /data?name=item (filter by name)
    console.log('Test 7: GET /data?name=item (filter by name)');
    const getByNameRes = await makeRequest('GET', '/data?name=item');
    assert(getByNameRes.status === 200, 'GET /data?name=item returns 200');
    assert(getByNameRes.body.count === 2, 'Name filter returns 2 entries (item-2, item-3)');
    console.log(`  Response: count=${getByNameRes.body.count}`);
    console.log('');

    // Test 8: GET /invalid (404 handler)
    console.log('Test 8: GET /invalid (404 handler)');
    const notFoundRes = await makeRequest('GET', '/invalid');
    assert(notFoundRes.status === 404, 'Invalid route returns 404');
    assert(notFoundRes.body.error === 'Not Found', 'Error message is "Not Found"');
    assert(Array.isArray(notFoundRes.body.availableRoutes), '404 includes available routes');
    console.log(`  Response: ${JSON.stringify(notFoundRes.body)}`);
    console.log('');

    // Test 9: GET /data?id=invalid (validation error)
    console.log('Test 9: GET /data?id=invalid (validation error)');
    const invalidIdRes = await makeRequest('GET', '/data?id=invalid');
    assert(invalidIdRes.status === 400, 'Invalid ID parameter returns 400');
    console.log(`  Response: ${JSON.stringify(invalidIdRes.body)}`);
    console.log('');

    // Summary
    console.log('='.repeat(60));
    console.log('TEST RESULTS');
    console.log('='.repeat(60));
    console.log(`[OK] Passed: ${testsPassed}`);
    console.log(`[X] Failed: ${testsFailed}`);
    console.log(`Total: ${testsPassed + testsFailed}`);
    console.log('');

    if (testsFailed === 0) {
      console.log('[OK] All tests passed!');
      process.exit(0);
    } else {
      console.log('[X] Some tests failed');
      process.exit(1);
    }

  } catch (error) {
    console.error('[X] Test suite error:', error.message);
    console.error('Is the server running? Start it with: node server.js');
    process.exit(1);
  }
}

// Run tests
runTests();
