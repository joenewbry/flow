/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        memex: {
          bg: '#0a0a0a',
          surface: '#141414',
          border: '#252525',
          text: '#e0e0e0',
          muted: '#666666',
          primary: '#7c6fe0',
          success: '#4ade80',
          error: '#f87171',
          warning: '#fbbf24',
        },
      },
    },
  },
  plugins: [],
}
