/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        holomed: {
          cyan: '#00ffff',
          dark: '#000000',
        },
      },
    },
  },
  plugins: [],
}
