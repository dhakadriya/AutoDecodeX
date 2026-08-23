import type { Metadata } from "next";
import { ThemeProvider } from "@/context/ThemeContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoDecodeX — AI Encoding Decoder",
  description: "Intelligent multi-layer encoding detection and decoding for CTF players and cybersecurity students.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var saved = localStorage.getItem('autodecodex_settings');
                  var theme = 'cyber';
                  if (saved) {
                    var parsed = JSON.parse(saved);
                    if (parsed.theme) {
                      theme = parsed.theme;
                    }
                  }
                  if (theme === 'system') {
                    var isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    theme = isDark ? 'dark' : 'light';
                  }
                  document.documentElement.setAttribute('data-theme', theme);
                } catch (e) {}
              })()
            `,
          }}
        />
      </head>
      <body className="scanlines cyber-grid min-h-screen">
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
