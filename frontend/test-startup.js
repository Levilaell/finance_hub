// Test script to check middleware behavior
const http = require('http');


// Simple server to test if the issue is with Next.js or general
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Test server running\n');
});

server.listen(3001, () => {
});

// Try to make a request after a delay
setTimeout(() => {
  http.get('http://localhost:3000', (res) => {
    res.on('data', (chunk) => {
    });
  }).on('error', (err) => {
  });
}, 2000);