/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#3D5FF0',
          50: '#EEF1FE',
          100: '#DCE2FD',
          200: '#B4C0FA',
          300: '#8B9EF7',
          400: '#637CF3',
          500: '#3D5FF0',
          600: '#2745D1',
          700: '#1E37A8',
          800: '#182B80',
          900: '#121F5C',
        },
        violet: {
          DEFAULT: '#8B5CF6',
          600: '#7C3AED',
        },
        sunset: {
          DEFAULT: '#FF8A4C',
          600: '#F2672B',
        },
        ink: {
          DEFAULT: '#0F1729',
          50: '#F5F7FB',
          100: '#E7EBF4',
          400: '#8993A8',
          500: '#5D6B85',
          700: '#232D45',
          800: '#151D30',
          900: '#0F1729',
        },
        mint: {
          DEFAULT: '#16A34A',
          600: '#0F8A3C',
        },
        amber: {
          DEFAULT: '#E29B0E',
          600: '#C4830A',
        },
        coral: {
          DEFAULT: '#EF4759',
          600: '#D8283C',
        },
        canvas: '#FAFBFF',
      },
      fontFamily: {
        display: ['"Outfit"', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        'card-float': '0 1px 2px rgba(15,23,41,0.04), 0 12px 32px -12px rgba(15,23,41,0.12)',
      },
      borderRadius: {
        xl2: '1.25rem',
      },
    },
  },
  plugins: [],
}

