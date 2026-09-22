import Link from "next/link";
import { ShieldCheck } from "lucide-react";

const links = [
  { href: "/", label: "Analyze" },
  { href: "/directory", label: "Community Index" },
];

/** Sticky top navigation bar shown on every page. */
export function NavBar() {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80 sticky top-0 z-10">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <ShieldCheck className="size-5 text-emerald-600" />
          <span>CyberSafe</span>
          <span className="hidden text-muted-foreground font-normal sm:inline">
            Dark Pattern Detector
          </span>
        </Link>
        <nav className="flex items-center gap-4 text-sm font-medium">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
