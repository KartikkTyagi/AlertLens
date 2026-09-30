import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: {
          25: "#FEFDFB",
          50: "#FAF8F5",
          100: "#F5F2EB",
          200: "#EFECE3",
          300: "#E2DDD2",
          400: "#D1C9BC",
          500: "#B8ADA0",
        },
        graphite: {
          50: "#F6F7F9",
          100: "#EBEEF2",
          200: "#D7DCE3",
          300: "#B3BAC6",
          400: "#8690A0",
          500: "#606A7B",
          600: "#485160",
          700: "#373E4A",
          800: "#262C35",
          900: "#1A1E24",
          950: "#111418",
        },
        crystal: {
          teal: "#0D9488",
          tealDark: "#0F766E",
          emerald: "#059669",
          amber: "#D97706",
          gold: "#B45309",
          rose: "#E11D48",
          purple: "#7C3AED",
        },
      },
      boxShadow: {
        crystal: "0 4px 20px -2px rgba(28, 25, 23, 0.04), 0 2px 6px -1px rgba(28, 25, 23, 0.02), inset 0 1px 0 0 rgba(255, 255, 255, 0.9)",
        "crystal-hover": "0 10px 30px -4px rgba(28, 25, 23, 0.08), 0 4px 10px -2px rgba(28, 25, 23, 0.04), inset 0 1px 0 0 rgba(255, 255, 255, 0.95)",
        "crystal-teal": "0 0 24px -2px rgba(13, 148, 136, 0.28), inset 0 1px 0 0 rgba(255, 255, 255, 0.3)",
        "crystal-dark": "0 12px 35px -5px rgba(17, 20, 24, 0.35), inset 0 1px 0 0 rgba(255, 255, 255, 0.12)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "Liberation Mono", "Courier New", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
