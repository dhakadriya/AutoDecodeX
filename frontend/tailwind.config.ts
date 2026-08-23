import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#0a0a0f",
          surface: "#0f0f1a",
          card: "#13131f",
          border: "#1e1e3a",
          green: "#00ff88",
          blue: "#00d4ff",
          purple: "#a855f7",
          pink: "#ff0080",
          yellow: "#ffd700",
          red: "#ff3333",
          muted: "#4a4a6a",
          text: "#c8c8e8",
        },
        theme: {
          bg: "var(--bg-app)",
          surface: "var(--bg-surface)",
          card: "var(--bg-card)",
          input: "var(--bg-input)",
          hover: "var(--bg-hover)",
          border: "var(--border-color)",
          borderGlow: "var(--border-color-glow)",
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
          accent: "var(--accent)",
          success: "var(--success)",
          warning: "var(--warning)",
          error: "var(--error)",
          info: "var(--info)",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'Fira Code'", "monospace"],
      },
      boxShadow: {
        "neon-green": "0 0 20px rgba(0, 255, 136, 0.4), 0 0 40px rgba(0, 255, 136, 0.1)",
        "neon-blue": "0 0 20px rgba(0, 212, 255, 0.4), 0 0 40px rgba(0, 212, 255, 0.1)",
        "neon-purple": "0 0 20px rgba(168, 85, 247, 0.4), 0 0 40px rgba(168, 85, 247, 0.1)",
        "neon-pink": "0 0 20px rgba(255, 0, 128, 0.4)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "scan": "scan 2s linear infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
        "typing": "typing 1s steps(1) infinite",
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        glow: {
          "0%": { textShadow: "0 0 10px #00ff88" },
          "100%": { textShadow: "0 0 20px #00ff88, 0 0 40px #00ff88" },
        },
        typing: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
