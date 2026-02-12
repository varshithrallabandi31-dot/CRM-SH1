"use client";

import "./globals.css";
import { Inter } from "next/font/google";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { usePathname } from 'next/navigation';
import { RoleProvider, useRole } from "@/context/RoleContext";

const inter = Inter({ subsets: ["latin"] });

function AppContent({ children }: { children: React.ReactNode }) {
  const { role, isAuthenticated, loading, logout } = useRole();
  const pathname = usePathname();

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-50">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (pathname === '/login') {
    return <main className="h-screen w-full">{children}</main>;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar role={role} />
      <div className="flex-1 flex flex-col ml-64">
        <Header currentRole={role} setRole={() => {}} />
        <main className="flex-1 overflow-y-auto mt-20 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-gray-50`}>
        <RoleProvider>
          <AppContent>{children}</AppContent>
        </RoleProvider>
      </body>
    </html>
  );
}
