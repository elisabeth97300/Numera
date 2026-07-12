/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F2F3EA",
        "paper-dim": "#E8EADD",
        ink: "#16231C",
        "ink-soft": "#3C4A40",
        rule: "#C3CDB4",
        "rule-strong": "#8FA07C",
        red: "#9C3B3B",
        forest: "#2C5235",
        "forest-dim": "#E4EBE0",
        gold: "#A9782E",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        body: ["IBM Plex Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
