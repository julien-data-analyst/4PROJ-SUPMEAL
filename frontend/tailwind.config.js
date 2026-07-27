/** @type {import('tailwindcss').Config} */
export default {
  content: [    './app.vue',
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './composables/**/*.{js,ts}',
    './plugins/**/*.{js,ts}',],
  theme: {
    extend: {
      colors: {
        'sup-light-green' : '#64FA16',
        'sup-dark-green' : '#1A7F02',
        'sup-light-gray' : '#F5F5F5',
        'sup-very-gray' : '#333333',
        'sup-red-error' : '#E74C3C',
        'sup-yellow-warning' : '#F1C40F',
        'sup-withe' : '#FFFFFF',
        'sup-border' : '#E0E0E0'
      },
    },
  },
  plugins: [],
}
