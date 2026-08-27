"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrainCircuit, CalendarDays, PlusCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { isMeetingDetailPath } from "@/lib/meeting-view";
import { MeetingViewDropdown } from "@/components/layout/meeting-view-dropdown";

const navItems = [
  {
    label: "Meetings",
    href: "/meetings",
    icon: CalendarDays,
    isActive: (pathname: string) =>
      pathname === "/" || (pathname.startsWith("/meetings") && pathname !== "/meetings/new"),
  },
  {
    label: "Upload transcript",
    href: "/meetings/new",
    icon: PlusCircle,
    isActive: (pathname: string) => pathname === "/meetings/new",
  },
];

export function Header() {
  const pathname = usePathname();
  const meetingPage = isMeetingDetailPath(pathname);

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-slate-200/80 bg-white/90 pt-[env(safe-area-inset-top,0px)] backdrop-blur-md">
      <div className="flex h-14 items-center gap-2 px-4 sm:gap-3 sm:px-5">
        <Link href="/meetings" className="flex min-w-0 shrink-0 items-center gap-2">
          <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-brand text-white">
            <BrainCircuit className="size-4" />
          </div>
          <p className="hidden truncate text-[15px] font-semibold tracking-tight text-ink sm:block">
            Smart Meet
          </p>
        </Link>

        <div className="mx-0.5 hidden h-5 w-px bg-slate-200 sm:block" />

        <nav className="flex min-w-0 items-center gap-0.5 overflow-x-auto">
          {navItems.map((item) => {
            const active = item.isActive(pathname);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "inline-flex h-9 shrink-0 items-center gap-1.5 rounded-lg px-2.5 text-sm font-medium transition sm:px-3",
                  active
                    ? "bg-brand-soft text-brand"
                    : "text-gray-600 hover:bg-page hover:text-ink",
                )}
              >
                <item.icon className="size-4" />
                {item.href === "/meetings/new" ? (
                  <>
                    <span className="sm:hidden">Upload</span>
                    <span className="hidden sm:inline">Upload transcript</span>
                  </>
                ) : (
                  item.label
                )}
              </Link>
            );
          })}
        </nav>

        {meetingPage ? (
          <div className="ml-auto min-w-0 shrink">
            <Suspense
              fallback={
                <span className="px-2 text-sm font-medium text-gray-600">Chat</span>
              }
            >
              <MeetingViewDropdown />
            </Suspense>
          </div>
        ) : null}
      </div>
    </header>
  );
}
