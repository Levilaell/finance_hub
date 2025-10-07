/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'lh3.googleusercontent.com',
      },
    ],
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
    const isDev = process.env.NODE_ENV === 'development';

    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // Script sources: Pluggy + Stripe + Meta Pixel (unsafe-inline needed for third-party widgets)
              isDev
                ? "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.pluggy.ai https://*.pluggy.ai https://js.stripe.com https://connect.facebook.net"
                : "script-src 'self' 'unsafe-inline' https://cdn.pluggy.ai https://*.pluggy.ai https://js.stripe.com https://connect.facebook.net",
              "style-src 'self' 'unsafe-inline' https://cdn.pluggy.ai https://*.pluggy.ai",
              "img-src 'self' data: blob: https://*.pluggy.ai https://*.pluggycdn.com https://lh3.googleusercontent.com https://www.facebook.com",
              "font-src 'self' data:",
              // Connect sources: API + Pluggy + Stripe + Meta Pixel (localhost only in dev)
              [
                "connect-src 'self'",
                isDev ? "http://localhost:8000" : "",
                "https://*.pluggy.ai https://api.pluggy.ai https://financehub-production.up.railway.app https://api.stripe.com https://www.facebook.com https://*.facebook.com"
              ].filter(Boolean).join(' '),
              // Frame sources: Pluggy + Stripe
              "frame-src 'self' https://*.pluggy.ai https://connect.pluggy.ai https://js.stripe.com https://*.stripe.com",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'"
            ].join('; ')
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'geolocation=(), microphone=(), camera=()'
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig