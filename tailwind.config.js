/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./lf-automator/webapp/templates/**/*.html",
    "./lf-automator/webapp/static/js/**/*.js",
    "./node_modules/flowbite/**/*.js"
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('flowbite/plugin')
  ],
}
