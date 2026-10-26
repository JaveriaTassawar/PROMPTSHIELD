// One short horizontal shake, used to draw attention to invalid fields on submit.
// Skipped when the user has asked the OS to reduce motion.
export function shake(element) {
  if (!element || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  element.animate(
    [
      { transform: 'translateX(0)' },
      { transform: 'translateX(-4px)' },
      { transform: 'translateX(4px)' },
      { transform: 'translateX(-3px)' },
      { transform: 'translateX(0)' },
    ],
    { duration: 300, easing: 'ease-out' },
  )
}
