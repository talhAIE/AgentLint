/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      keyframes: {
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        }
      },
      colors: {
        base: '#0B0F19', // Deep navy background
        surface: '#111827', // Sidebar / card background
        elevated: '#1F2937',
        border: '#1E293B',
        accent: {
          cyan: '#00D8FF',
          blue: '#3B82F6',
          teal: '#10B981',
          purple: '#8B5CF6',
          pink: '#EC4899',
          orange: '#F59E0B'
        },
        text: {
          primary: '#F9FAFB',
          muted: '#9CA3AF'
        },
        severity: {
          critical: '#F43F5E',
          high: '#F97316',
          warn: '#F59E0B',
          info: '#3B82F6'
        },
      }
    },
  },
  plugins: [],
}
