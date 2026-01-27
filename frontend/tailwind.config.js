/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        primary: '#564D4D',    // Dark Grey (Main Brand Color)
        secondary: '#FFFFFF',
        accent: '#0081A7',     // Deep Blue (Secondary Actions)
        highlight: '#00AFB9',  // Teal
        success: '#22C55E',
        warning: '#F59E0B',
        error: '#EF4444',
        
        // Dark Mode specific backgrounds
        dark: {
          bg: '#1a1a1a',
          surface: '#2d2d2d',
          border: '#404040'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}