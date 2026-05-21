import type { Metadata } from "next";
import { Outfit, JetBrains_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Providers } from "./providers/Providers";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Krafzen AI — Reimagine Design with AI-Powered Precision",
  description: "Voice-to-CAD AI that converts spoken design briefs into production-ready DWG, DXF, and Revit drawings.",
  icons: {
    icon: "/icon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const isProduction = process.env.NODE_ENV === "production";

  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${outfit.variable} ${jetbrainsMono.variable} antialiased`}
        suppressHydrationWarning
      >
        {isProduction && (
          <>
            <Script
              async
              src="https://www.googletagmanager.com/gtag/js?id=G-X04TFTSM32"
              strategy="afterInteractive"
            />
            <Script id="google-analytics-init" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', 'G-X04TFTSM32');
              `}
            </Script>
            <Script
              async
              src="https://assets.endorsely.com/endorsely.js"
              data-endorsely="6546fb55-6ca1-4057-831d-c550a9da4cc0"
              strategy="afterInteractive"
            />
          </>
        )}
        <ToastContainer position="top-center" className="z-999999" />
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
