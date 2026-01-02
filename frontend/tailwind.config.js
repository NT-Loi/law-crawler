/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'legal-blue': '#003366',
                'legal-gold': '#C5A059',
            }
        },
    },
    plugins: [],
}
