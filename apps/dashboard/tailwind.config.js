/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bull: '#10b981',  // green
        bear: '#ef4444',  // red
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
