import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Orders Dashboard",
  description: "Browse and export orders",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-white text-zinc-900 antialiased">{children}</body>
    </html>
  );
}
