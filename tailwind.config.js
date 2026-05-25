/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			fontFamily: {
				sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
			},
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
					DEFAULT: '#1B3A5C',
					light:   '#2A5280',
					dark:    '#0F2238',
					subtle:  '#E8EEF5'
				}
			}
		}
	},
	plugins: []
};
