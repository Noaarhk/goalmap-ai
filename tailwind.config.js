/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{ts,tsx}"],
	darkMode: "class",
	theme: {
		extend: {
			fontFamily: {
				sans: ["Inter", "sans-serif"],
			},
			animation: {
				shimmer: "shimmer 1.5s infinite",
			},
			keyframes: {
				shimmer: {
					"0%": { transform: "translateX(-100%)" },
					"100%": { transform: "translateX(100%)" },
				},
			},
		},
	},
	plugins: [],
};
