// Standard heading block for app pages: cyan eyebrow, title, optional
// description and right-hand actions. Also sets the browser tab title.
function PageHeader({ eyebrow, title, description, children }) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <title>{`${title} · PromptShield`}</title>
      <div>
        {eyebrow && <p className="font-mono text-xs tracking-widest text-cyan/80 uppercase">{eyebrow}</p>}
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-fg sm:text-3xl">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-fg-muted">{description}</p>}
      </div>
      {children}
    </header>
  )
}

export default PageHeader
