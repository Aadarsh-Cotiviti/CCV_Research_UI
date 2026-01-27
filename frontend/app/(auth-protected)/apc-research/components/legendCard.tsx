export const LEGEND: Record<string, { label: string; color: string; description: string }> = {
  internal_kb: {
    label: "Internal KB",
    color: "emerald-500",
    description: "Validated knowledge base source",
  },
  llm: {
    label: "LLM Generated",
    color: "stone-500",
    description: "Drafted by the model",
  },
};

export const LegendCard = () => {
  return (
    <section
      aria-label="Source legend"
      className="flex flex-wrap items-center gap-4 rounded-xl border border-white/10 bg-sidebar px-4 py-3 text-sm text-sidebar-foreground"
    >
      <h3 className="text-xs font-semibold uppercase tracking-wide text-sidebar-foreground/80">
        Sources
      </h3>
      <ul className="flex flex-wrap items-center gap-3">
        {Object.entries(LEGEND).map(([key, item]) => (
          <li key={key} className="flex items-center gap-2">
            <span className={`inline-block size-4 rounded-sm bg-${item.color}`} aria-hidden />
            <div className="leading-tight">
              <div className="font-medium">{item.label}</div>
              <p className="text-xs text-sidebar-foreground/80">{item.description}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
};
