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
        // Minimalist grayscale system - only grays needed
        gray: {
          50: 'hsl(0 0% 98%)',
          100: 'hsl(0 0% 94%)',
          200: 'hsl(0 0% 88%)',
          300: 'hsl(0 0% 82%)',
          400: 'hsl(0 0% 65%)',
          500: 'hsl(0 0% 50%)',
          600: 'hsl(0 0% 35%)',
          700: 'hsl(0 0% 18%)',
          800: 'hsl(0 0% 12%)',
          900: 'hsl(0 0% 6%)',
          950: 'hsl(0 0% 2%)',
        },
        // Semantic colors - minimal and professional
        success: 'hsl(120 60% 40%)',
        warning: 'hsl(45 90% 40%)',
        error: 'hsl(0 60% 45%)',
        info: 'hsl(220 60% 45%)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
export default config