import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AUMOv3 — Smart Mobility for Maharashtra",
  description: "AI-powered carpooling, eco-routing, and real-time traffic for Maharashtra",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossOrigin="" />
      </head>
      <body className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
        {children}
      </body>
    </html>
  );
}
