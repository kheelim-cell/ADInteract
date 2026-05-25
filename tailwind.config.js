/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				brand: {
					50:  '#fdf8ec',
					100: '#faf0ca',
					200: '#f3dc8e',
					300: '#eac34a',
					400: '#dda827',
					500: '#c58a15',
					600: '#a86d11',
					700: '#865410',
					800: '#6e4212',
					900: '#5c3712',
					950: '#331d06'
				},
				navy: {
					DEFAULT: '#0A1628',
					light:   '#14253f',
					dark:    '#060e1a'
				}
			}
		}
	},
	plugins: []
};
