import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OnLooker",
  description: "Real-time presentation coaching with simulated audiences",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
