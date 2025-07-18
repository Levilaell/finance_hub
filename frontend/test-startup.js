// Test script to check middleware behavior
const http = require('http');

console.log('Testing server startup...');

// Simple server to test if the issue is with Next.js or general
const server = http.createServer((req, res) => {
  console.log(`Request received: ${req.method} ${req.url}`);
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Test server running\n');
});

server.listen(3001, () => {
  console.log('Test server running on http://localhost:3001');
});

// Try to make a request after a delay
setTimeout(() => {
  console.log('Making test request to localhost:3000...');
  http.get('http://localhost:3000', (res) => {
    console.log(`Response status: ${res.statusCode}`);
    res.on('data', (chunk) => {
      console.log(`Response data: ${chunk}`);
    });
  }).on('error', (err) => {
    console.error(`Request error: ${err.message}`);
  });
}, 2000);