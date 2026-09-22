import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { NavBar } from "@/components/shared/NavBar";
import { AmbientBackground } from "@/components/shared/AmbientBackground";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CyberSafe — Dark Pattern & Hidden Fee Detector",
  description:
    "Analyze websites for deceptive dark patterns and hidden recurring fees. Report and track community-validated safety data.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 dark:bg-slate-950">
        <AmbientBackground />
        <NavBar />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
