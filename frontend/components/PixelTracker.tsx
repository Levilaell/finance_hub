'use client';
import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';

export const PIXEL_ID = '24169428459391565';

export default function PixelTracker() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    const isDev = process.env.NODE_ENV === 'development';

    // Inject Facebook Pixel script
    if (typeof window !== 'undefined' && !window.fbq) {
      if (isDev) console.log('[Meta Pixel] Initializing pixel...');

      (function(f: any, b: any, e: any, v: any, n: any, t: any, s: any) {
        if (f.fbq) return;
        n = f.fbq = function() {
          n.callMethod
            ? n.callMethod.apply(n, arguments)
            : n.queue.push(arguments);
        };
        if (!f._fbq) f._fbq = n;
        n.push = n;
        n.loaded = true;
        n.version = '2.0';
        n.queue = [];
        t = b.createElement(e);
        t.async = true;
        t.src = v;
        s = b.getElementsByTagName(e)[0];
        s.parentNode.insertBefore(t, s);
      })(
        window,
        document,
        'script',
        'https://connect.facebook.net/en_US/fbevents.js',
        undefined,
        undefined,
        undefined
      );

      // Initialize pixel after script loads
      const initInterval = setInterval(() => {
        if (window.fbq && typeof window.fbq === 'function') {
          window.fbq('init', PIXEL_ID);
          if (isDev) console.log('[Meta Pixel] Pixel initialized with ID:', PIXEL_ID);
          clearInterval(initInterval);
        }
      }, 100);

      // Clear interval after 5 seconds max
      setTimeout(() => clearInterval(initInterval), 5000);
    }

    // Track PageView on mount and route changes
    if (window.fbq) {
      window.fbq('track', 'PageView');
      if (isDev) console.log('[Meta Pixel] PageView tracked for:', pathname);
    }
  }, [pathname, searchParams]);

  return null;
}
