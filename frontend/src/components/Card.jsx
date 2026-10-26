// Frosted surface used for panels and cards. `glow` adds the violet brand halo —
// keep it for the one primary card on a screen. `borderClassName` replaces the
// default border colour (passing a second border colour in className would
// depend on CSS order).
function Card({ glow = false, borderClassName = 'border-border/80', className = '', children, ...props }) {
  return (
    <div className={`glass rounded-card border ${borderClassName} ${glow ? 'shadow-glow' : 'shadow-card'} ${className}`} {...props}>
      {children}
    </div>
  )
}

export default Card
