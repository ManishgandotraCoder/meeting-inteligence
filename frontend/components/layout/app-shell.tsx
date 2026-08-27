import { Header } from "@/components/layout/header";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <Header />
      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto pt-[var(--header-h)] pb-[env(safe-area-inset-bottom,0px)]">
        {children}
      </div>
    </div>
  );
}
