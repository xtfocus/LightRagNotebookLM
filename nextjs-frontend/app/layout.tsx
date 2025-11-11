import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import ClientCopilotKitWrapper from "./ClientCopilotKitWrapper";
import { NotificationProvider } from "@/components/ui/NotificationContext";
import { RouteProgress } from "@/components/ui/RouteProgress";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { AuthProvider } from "@/contexts/AuthContext";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "OpenStorm - Research anything",
  description: "OpenStorm - Research anything",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <RouteProgress />
        <ErrorBoundary>
          <AuthProvider>
        <NotificationProvider>
          <ClientCopilotKitWrapper>
            {children}
          </ClientCopilotKitWrapper>
        </NotificationProvider>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
