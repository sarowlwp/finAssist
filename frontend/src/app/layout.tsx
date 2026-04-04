import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "私人投资 AI 助理",
  description: "多Agent驱动的金融分析认知增强工具",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <Sidebar />
        <main className="ml-64 min-h-screen p-8">{children}</main>
      </body>
    </html>
  );
}
