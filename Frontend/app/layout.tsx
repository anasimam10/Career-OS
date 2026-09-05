import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { NavBar } from "@/components/layout/NavBar"
import { Footer } from "@/components/layout/Footer"
import { BackendWarmup } from "@/components/shared/BackendWarmup"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })

export const metadata: Metadata = {
  title: "Career OS — Career Operating System",
  description:
    "An AI-powered student career journey that helps you explore options, understand the reality of a field, and take your next step with confidence.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="min-h-screen flex flex-col bg-background font-sans antialiased text-foreground">
        <BackendWarmup />
        <NavBar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
