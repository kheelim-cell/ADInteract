/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			fontFamily: {
				sans: ['Manrope', 'system-ui', 'sans-serif'],
			},
			colors: {
				brand: {
					50:  '#fdf9ed',
					100: '#faf2d2',
					200: '#f4e29e',
					300: '#ebcc65',
					400: '#dfb83c',
					500: '#C8A951',
					600: '#a88535',
					700: '#86682a',
					800: '#6b5222',
					900: '#594420',
					950: '#31240d'
				},
				navy: {
					DEFAULT: '#1B4332',
					light:   '#2D6A4F',
					dark:    '#0F2B1F',
					subtle:  '#EAF2ED'
				}
			}
		}
	},
	plugins: []
};
