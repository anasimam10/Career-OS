import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { NavBar } from "@/components/layout/NavBar"
import { Footer } from "@/components/layout/Footer"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })

export const metadata: Metadata = {
  title: "A&H Careers — AI Student Career Journey",
  description:
    "An AI-powered student career journey that helps you explore options, understand the reality of a field, and take your next step with confidence.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col bg-background font-sans antialiased">
        <NavBar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
