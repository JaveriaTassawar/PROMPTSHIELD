import { NavLink } from 'react-router-dom'
import { NAV_ITEMS } from '../config/navigation.js'

// Main navigation list, shared by the desktop sidebar and the mobile drawer.
// NavLink marks the current route with aria-current="page".
function SidebarNav({ onNavigate }) {
  return (
    <nav aria-label="Main">
      <p className="px-3 font-mono text-[10px] tracking-widest text-fg-subtle uppercase">Workspace</p>
      <ul className="mt-2 flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 rounded-control px-3 py-2 text-sm font-medium transition duration-150 ease-snappy ${
                  isActive ? 'bg-primary/15 text-fg' : 'text-fg-muted hover:bg-surface-raised/70 hover:text-fg'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    aria-hidden="true"
                    className={`absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-accent shadow-[0_0_8px_rgb(167_139_250/0.8)] transition-transform duration-200 ease-snappy ${
                      isActive ? 'scale-y-100' : 'scale-y-0'
                    }`}
                  />
                  <item.icon
                    className={`h-4.5 w-4.5 shrink-0 transition duration-150 ease-snappy group-hover:translate-x-0.5 ${
                      isActive ? 'text-accent' : 'text-fg-subtle group-hover:text-fg-muted'
                    }`}
                  />
                  {item.label}
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}

export default SidebarNav
