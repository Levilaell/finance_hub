import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        // Finance Hub specific colors - CaixaHub inspired
        gradient: {
          start: 'hsl(var(--gradient-start))',
          end: 'hsl(var(--gradient-end))',
        },
        // Vibrant purple palette
        purple: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#b146ff', // Primary vibrant purple
          600: '#9333ea',
          700: '#8b2eff', // Light mode primary
          800: '#6b21a8',
          900: '#581c87',
          950: '#3b0764',
        },
        // Vibrant magenta/pink palette
        magenta: {
          400: '#ff6bb5',
          500: '#ff3b9e', // Accent vibrant magenta
          600: '#ff2e85', // Light mode accent
          700: '#e91e73',
          800: '#cc1862',
        },
        // Dark backgrounds
        dark: {
          DEFAULT: '#0a0a0a', // Main dark background
          100: '#14101a', // Card background
          200: '#1a1424', // Popover background
          300: '#1f1b2e', // Secondary background
          400: '#2b2439', // Border color
        },
        // Semantic colors - professional and subtle
        success: '#16a34a',
        info: '#2563eb',
        warning: '#ca8a04',
        error: 'hsl(0, 40%, 45%)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
export default config