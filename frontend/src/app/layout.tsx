import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoDecodeX — AI Encoding Decoder",
  description: "Intelligent multi-layer encoding detection and decoding for CTF players and cybersecurity students.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="scanlines cyber-grid min-h-screen">
        {children}
      </body>
    </html>
  );
}
