/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0a0e17',
        surface: '#111827',
        'surface-2': '#1a2332',
        border: '#1e3a5f',
        accent: '#0ea5e9',
        'accent-glow': 'rgba(14, 165, 233, 0.15)',
        text: '#e2e8f0',
        'text-dim': '#94a3b8',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
      },
      backgroundImage: {
        'gradient-accent': 'linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)',
      },
      animation: {
        'spin-slow': 'spin 1.5s linear infinite',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(14, 165, 233, 0.4)' },
          '50%': { boxShadow: '0 0 20px 4px rgba(14, 165, 233, 0.3)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
    },
  },
  plugins: [],
}
