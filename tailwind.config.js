/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				brand: {
					50: '#f0f7ff',
					100: '#e0effe',
					200: '#bae0fd',
					300: '#7cc8fc',
					400: '#36adf8',
					500: '#0c93e9',
					600: '#0074c7',
					700: '#015da1',
					800: '#064f85',
					900: '#0b426e',
					950: '#072a49'
				}
			}
		}
	},
	plugins: []
};
