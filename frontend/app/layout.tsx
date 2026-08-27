import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "@/app/globals.css";
import { AppShell } from "@/components/layout/app-shell";

const sans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-ui",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Smart Meet",
    template: "%s | Smart Meet",
  },
  description: "AI-powered meeting transcript intelligence.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={sans.variable}>
      <body className="h-dvh overflow-hidden font-sans antialiased">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
