import { useState } from 'react'
import FormField from './FormField.jsx'
import { EyeIcon, EyeOffIcon, LockIcon } from './icons.jsx'

// Password input with a show/hide toggle. Only the input's `type` changes —
// the value, validation and form submission are untouched.
function PasswordField(props) {
  const [visible, setVisible] = useState(false)

  const toggle = (
    <button
      type="button"
      onClick={() => setVisible((v) => !v)}
      aria-label={visible ? 'Hide password' : 'Show password'}
      aria-pressed={visible}
      aria-controls={props.id}
      className="rounded-control p-2 text-fg-subtle transition-colors hover:text-fg"
    >
      {visible ? <EyeOffIcon className="h-4.5 w-4.5" /> : <EyeIcon className="h-4.5 w-4.5" />}
    </button>
  )

  return <FormField {...props} type={visible ? 'text' : 'password'} icon={LockIcon} trailing={toggle} />
}

export default PasswordField
