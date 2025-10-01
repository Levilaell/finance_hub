/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  
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
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // Script sources: Pluggy + Stripe
              process.env.NODE_ENV === 'development'
                ? "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.pluggy.ai https://*.pluggy.ai https://js.stripe.com"
                : "script-src 'self' 'unsafe-inline' https://cdn.pluggy.ai https://*.pluggy.ai https://js.stripe.com",
              "style-src 'self' 'unsafe-inline' https://cdn.pluggy.ai https://*.pluggy.ai",
              "img-src 'self' data: blob: https://*.pluggy.ai https://*.pluggycdn.com",
              "font-src 'self' data:",
              // Connect sources: API + Pluggy + Stripe
              "connect-src 'self' http://localhost:8000 https://*.pluggy.ai https://api.pluggy.ai https://financehub-production.up.railway.app https://api.stripe.com",
              // Frame sources: Pluggy + Stripe
              "frame-src 'self' https://*.pluggy.ai https://connect.pluggy.ai https://js.stripe.com https://*.stripe.com",
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