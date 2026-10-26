import { useEffect, useRef, useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import Logo from './Logo.jsx'
import PreviewStatus from './PreviewStatus.jsx'
import SidebarNav from './SidebarNav.jsx'
import { MenuIcon, XIcon } from './icons.jsx'
import { NAV_ITEMS } from '../config/navigation.js'

// Layout route for the signed-in app (Task 74). Wide screens (lg and up) get a
// persistent sidebar; narrower screens get a top bar with a slide-in drawer.
// Route protection arrives with Task 73.
function AppLayout() {
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuButtonRef = useRef(null)
  const closeButtonRef = useRef(null)

  const closeMenu = () => setMenuOpen(false)

  // Section name for the mobile top bar, from the sidebar's own entries
  // (e.g. /simulation/sim-01 → Simulation Lab). Routes outside the nav show none.
  const currentSection = NAV_ITEMS.find(
    (item) => location.pathname === item.to || location.pathname.startsWith(`${item.to}/`),
  )

  // While the drawer is open: focus its close button, close on Escape or when the
  // window grows to desktop width, and lock page scroll. On close, focus returns
  // to the menu button.
  useEffect(() => {
    if (!menuOpen) return

    const menuButton = menuButtonRef.current
    closeButtonRef.current?.focus()

    const onKeyDown = (event) => {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    const desktop = window.matchMedia('(min-width: 1024px)')
    const onResize = (event) => {
      if (event.matches) setMenuOpen(false)
    }
    const previousOverflow = document.body.style.overflow

    document.addEventListener('keydown', onKeyDown)
    desktop.addEventListener('change', onResize)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', onKeyDown)
      desktop.removeEventListener('change', onResize)
      document.body.style.overflow = previousOverflow
      menuButton?.focus()
    }
  }, [menuOpen])

  return (
    <div className="min-h-screen">
      <a
        href="#main-content"
        className="sr-only rounded-control bg-primary px-3 py-2 text-sm font-semibold text-white focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50"
      >
        Skip to content
      </a>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border/60 bg-canvas/70 backdrop-blur-md lg:flex">
        <div className="px-5 py-5">
          <Link to="/dashboard" className="inline-block rounded-control">
            <Logo />
          </Link>
        </div>
        <div className="flex-1 overflow-y-auto px-3 pt-2 pb-5">
          <SidebarNav />
        </div>
        <div className="border-t border-border/60 px-4 py-4">
          <PreviewStatus />
        </div>
      </aside>

      {/* Everything behind the drawer is inert while it is open */}
      <div inert={menuOpen} className="lg:pl-60">
        {/* Mobile / tablet top bar */}
        <header className="glass sticky top-0 z-20 flex items-center gap-3 border-b border-border/60 px-4 py-3 lg:hidden">
          <button
            ref={menuButtonRef}
            type="button"
            onClick={() => setMenuOpen(true)}
            aria-label="Open navigation menu"
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
            className="rounded-control p-2 text-fg-muted transition-colors hover:bg-surface-raised hover:text-fg"
          >
            <MenuIcon className="h-5 w-5" />
          </button>
          <Link to="/dashboard" className="shrink-0 rounded-control">
            <Logo />
          </Link>
          {currentSection && (
            <>
              <span className="h-5 w-px shrink-0 bg-border" aria-hidden="true" />
              <span className="min-w-0 truncate text-sm font-medium text-fg-muted">{currentSection.label}</span>
            </>
          )}
          <PreviewStatus compact className="ml-auto hidden shrink-0 sm:inline-flex" />
        </header>

        <main id="main-content" tabIndex={-1} className="mx-auto w-full max-w-6xl px-4 py-6 focus:outline-none sm:px-6 lg:px-10 lg:py-10">
          <div key={location.pathname} className="animate-fade-up">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile / tablet drawer. Visibility flips after the slide-out finishes so
          the closed drawer is not focusable. */}
      <div
        className={`fixed inset-0 z-40 transition-[visibility] duration-300 lg:hidden ${menuOpen ? 'visible' : 'invisible'}`}
      >
        <div
          aria-hidden="true"
          onClick={closeMenu}
          className={`absolute inset-0 bg-canvas/70 backdrop-blur-sm transition-opacity duration-300 ${menuOpen ? 'opacity-100' : 'opacity-0'}`}
        />
        <div
          id="mobile-nav"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
          className={`absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col border-r border-border/60 bg-canvas/95 px-3 py-4 shadow-glow backdrop-blur-md transition-transform duration-300 ease-snappy ${
            menuOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <div className="mb-4 flex items-center justify-between px-2">
            <Logo />
            <button
              ref={closeButtonRef}
              type="button"
              onClick={closeMenu}
              aria-label="Close navigation menu"
              className="rounded-control p-2 text-fg-muted transition-colors hover:bg-surface-raised hover:text-fg"
            >
              <XIcon className="h-5 w-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <SidebarNav onNavigate={closeMenu} />
          </div>
          <div className="border-t border-border/60 px-2 pt-4">
            <PreviewStatus />
          </div>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
