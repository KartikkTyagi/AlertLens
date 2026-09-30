"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Layers,
  Bell,
  ClipboardList,
  LogOut,
  User as UserIcon,
  LogIn,
  Shield,
  Zap,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, isAdmin, logout } = useAuth();

  const navLinks = [
    { href: "/", label: "Command Center", icon: Layers },
    { href: "/alerts", label: "Telemetry Stream", icon: Bell },
  ];

  if (isAdmin) {
    navLinks.push({ href: "/audit-log", label: "Audit Ledger", icon: ClipboardList });
  }

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 bg-white/85 backdrop-blur-md border-b border-ivory-300/80 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Left Navigation */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-3 group">
            {/* Geometric Crystalline Mark */}
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-700 via-teal-600 to-amber-600 flex items-center justify-center text-white shadow-crystal-teal group-hover:scale-105 transition-transform duration-200">
              <Shield className="w-5 h-5 drop-shadow-xs" />
            </div>

            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-lg tracking-tight text-graphite-950 font-sans">
                  AlertLens
                </span>
                <span className="text-[10px] font-mono font-bold tracking-wider px-1.5 py-0.5 rounded-md bg-ivory-200 text-teal-800 border border-ivory-300">
                  SOC v2.4
                </span>
              </div>
              <p className="text-[11px] text-graphite-500 -mt-0.5 tracking-wide">
                Autonomous Incident Intelligence
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5 pl-6 border-l border-ivory-300">
            {navLinks.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));
              return (
                <Link
                  key={href}
                  href={href}
                  className={`relative flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all ${
                    isActive
                      ? "bg-ivory-100 text-graphite-950 shadow-xs border border-ivory-300"
                      : "text-graphite-600 hover:text-graphite-900 hover:bg-ivory-50"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-teal-700" : "text-graphite-400"}`} />
                  <span>{label}</span>
                  {isActive && (
                    <span className="absolute -bottom-[13px] left-1/2 -translate-x-1/2 w-5 h-[2px] bg-teal-600 rounded-full" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Section: Auth & Role Info */}
        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-ivory-50/90 border border-ivory-300/80 shadow-2xs">
                <div className="w-6 h-6 rounded-full bg-graphite-100 text-graphite-700 flex items-center justify-center text-xs font-bold">
                  <UserIcon className="w-3.5 h-3.5" />
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-graphite-900 font-mono">
                    {user.username}
                  </span>
                  <span
                    className={`text-[9px] font-mono font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md ${
                      isAdmin
                        ? "bg-purple-100 text-purple-800 border border-purple-200"
                        : "bg-teal-100 text-teal-800 border border-teal-200"
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
              </div>

              <button
                onClick={handleLogout}
                title="Log out"
                className="p-2 text-graphite-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors border border-transparent hover:border-rose-100"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors tactile-button"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Portal Sign In</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};
