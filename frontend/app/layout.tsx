import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "AlertLens — SOC Alert Triage & Incident Intelligence",
  description: "Autonomous SIEM noise reduction and incident correlation using semantic graph clustering and Groq AI briefs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-ivory-50 text-graphite-900 font-sans selection:bg-teal-500/20 selection:text-teal-900 flex flex-col antialiased">
        <AuthProvider>
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
          <footer className="border-t border-ivory-300/80 bg-white/70 backdrop-blur-md py-6 text-center text-xs text-graphite-500">
            <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-graphite-800">AlertLens</span>
                <span className="text-ivory-400">•</span>
                <span>Autonomous Security Operations Center Intelligence</span>
              </div>
              <span className="font-mono text-[11px] text-graphite-400">
                Semantic Graph Clustering • Deterministic Scoring • Groq AI Intelligence Briefs
              </span>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
