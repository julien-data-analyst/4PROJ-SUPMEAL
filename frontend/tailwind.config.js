/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './app/app.vue',
    './app/components/**/*.{vue,js,ts}',
    './app/layouts/**/*.vue',
    './app/pages/**/*.vue',
    './app/composables/**/*.{js,ts}',
    './app/plugins/**/*.{js,ts}',
  ],
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
