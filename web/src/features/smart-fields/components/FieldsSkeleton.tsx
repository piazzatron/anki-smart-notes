export const FieldsSkeleton = () => (
  <div aria-label="Loading Smart Fields" className="space-y-5 px-6 py-5">
    {[0, 1].map((group) => (
      <div className="animate-pulse" key={group}>
        <div className="mb-2.5 h-2.5 w-20 rounded bg-white/[0.05]" />
        <div className="overflow-hidden rounded-lg border border-white/[0.06]">
          <div className="h-11 border-b border-white/[0.05] bg-white/[0.025]" />
          <div className="space-y-2 p-3">
            <div className="h-5 rounded bg-white/[0.025]" />
            <div className="h-5 rounded bg-white/[0.025]" />
          </div>
        </div>
      </div>
    ))}
  </div>
)
