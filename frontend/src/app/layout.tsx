import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { ThemeProvider } from "@/components/providers/theme-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "私人投资 AI 助理",
  description: "多Agent驱动的金融分析认知增强工具",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider defaultTheme="light" storageKey="theme">
          <Sidebar />
          <main className="ml-64 min-h-screen p-6">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
