// Fixed, decorative backdrop for every page: dot grid plus two slowly drifting
// violet/indigo glows. Drawn with gradients rather than blur filters to stay cheap.
function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div className="absolute inset-0 bg-grid" />
      <div className="absolute -top-40 -left-40 h-[36rem] w-[36rem] animate-drift rounded-full bg-[radial-gradient(circle,rgb(124_58_237/0.22),transparent_65%)]" />
      <div
        className="absolute -right-48 -bottom-48 h-[40rem] w-[40rem] animate-drift rounded-full bg-[radial-gradient(circle,rgb(79_70_229/0.18),transparent_65%)]"
        style={{ animationDelay: '-18s' }}
      />
    </div>
  )
}

export default AmbientBackground
