/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',
  
  // Disable type checking during build to avoid hanging
  typescript: {
    ignoreBuildErrors: true,
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`
          : 'http://localhost:8000/api/:path*',
      },
    ]
  },
  async headers() {
    return [
      {
        source: '/flutter_service_worker.js',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
        ],
      },
      {
        // Aplicar CSP mais permissiva para páginas que usam Pluggy
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.pluggy.ai https://*.pluggy.ai",
              "style-src 'self' 'unsafe-inline' https://cdn.pluggy.ai https://*.pluggy.ai",
              "img-src 'self' data: blob: https://*.pluggy.ai https://*.pluggycdn.com",
              "font-src 'self' data:",
              "connect-src 'self' http://localhost:8000 https://*.pluggy.ai https://api.pluggy.ai https://finance-backend-production-29df.up.railway.app",
              "frame-src 'self' https://*.pluggy.ai https://connect.pluggy.ai",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'"
            ].join('; ')
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig