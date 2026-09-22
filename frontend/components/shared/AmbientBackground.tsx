export function AmbientBackground() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
    >
      {/* Forensic-grid canvas spanning the full viewport */}
      <div
        className="absolute inset-0 opacity-[0.04] dark:opacity-[0.06] animate-grid-drift"
        style={{
          backgroundImage:
            "linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      {/* Ambient glows — slate/emerald only, kept faint enough to never affect text contrast */}
      <div className="absolute left-1/2 top-[-10%] size-[36rem] -translate-x-1/2 rounded-full bg-emerald-500/6 blur-3xl animate-glow-pulse dark:bg-emerald-400/6" />
      <div className="absolute right-[-6%] bottom-[-8%] size-[28rem] rounded-full bg-slate-400/6 blur-3xl dark:bg-slate-300/4" />
    </div>
  );
}
