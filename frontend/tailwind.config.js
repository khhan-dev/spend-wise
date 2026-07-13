/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ledger: {
          DEFAULT: "#1C6B4B",
          dark: "#12513A",
          soft: "#E6F0EA",
        },
        seal: "#AE3A2D",
        ink: "#15201A",
        paper: "#F5F7F3",
      },
      fontFamily: {
        sans: ['"Pretendard Variable"', "Pretendard", "-apple-system", '"Malgun Gothic"', "sans-serif"],
        mono: ['"SF Mono"', "Consolas", '"D2Coding"', "monospace"],
      },
    },
  },
  plugins: [],
};
