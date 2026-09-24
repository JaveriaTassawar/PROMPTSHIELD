import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../components/Alert.jsx'
import Button from '../components/Button.jsx'
import FormField from '../components/FormField.jsx'
import PasswordField from '../components/PasswordField.jsx'
import { MailIcon } from '../components/icons.jsx'
import { mockLogin } from '../mocks/auth.js'
import { shake } from '../utils/motion.js'
import { isValidEmail } from '../utils/validation.js'

function validate({ email, password }) {
  const errors = {}
  if (!email.trim()) {
    errors.email = 'Email is required.'
  } else if (!isValidEmail(email)) {
    errors.email = 'Enter a valid email address.'
  }
  if (!password) {
    errors.password = 'Password is required.'
  }
  return errors
}

function LoginPage() {
  const [values, setValues] = useState({ email: '', password: '' })
  const [submitted, setSubmitted] = useState(false)
  const [status, setStatus] = useState('idle') // idle | submitting | success | error
  const emailRef = useRef(null)
  const passwordRef = useRef(null)

  // Errors only show after the first submit, then track edits live.
  const errors = submitted ? validate(values) : {}

  function handleChange(event) {
    const { name, value } = event.target
    setValues((prev) => ({ ...prev, [name]: value }))
    if (status === 'error' || status === 'success') setStatus('idle')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitted(true)

    const currentErrors = validate(values)
    const invalid = [
      ['email', emailRef],
      ['password', passwordRef],
    ].filter(([field]) => currentErrors[field])
    if (invalid.length > 0) {
      invalid.forEach(([, ref]) => shake(ref.current.closest('[data-field]')))
      invalid[0][1].current.focus()
      return
    }

    setStatus('submitting')
    try {
      await mockLogin()
      setStatus('success')
    } catch {
      setStatus('error')
    }
  }

  const isSubmitting = status === 'submitting'

  return (
    <>
      <div className="animate-fade-up" style={{ animationDelay: '60ms' }}>
        <h1 className="text-3xl font-bold tracking-tight text-fg">Welcome back</h1>
        <p className="mt-2 text-fg-muted">Sign in to your PromptShield account.</p>
      </div>

      <div className="mt-6 animate-fade-up" style={{ animationDelay: '120ms' }}>
        {status === 'error' && (
          <Alert variant="error" className="mb-4">
            Invalid email or password.
          </Alert>
        )}
        {status === 'success' && (
          <Alert variant="success" className="mb-4">
            Mock sign-in succeeded — no account was checked. Real login is wired in Task 72.
          </Alert>
        )}

        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <FormField
            id="email"
            name="email"
            type="email"
            label="Email Address"
            autoComplete="email"
            placeholder="you@example.com"
            icon={MailIcon}
            value={values.email}
            onChange={handleChange}
            error={errors.email}
            ref={emailRef}
          />
          <PasswordField
            id="password"
            name="password"
            label="Password"
            autoComplete="current-password"
            value={values.password}
            onChange={handleChange}
            error={errors.password}
            ref={passwordRef}
          />

          <Button type="submit" loading={isSubmitting} className="mt-1 w-full">
            {isSubmitting ? 'Signing in…' : 'Sign In'}
          </Button>
        </form>
      </div>

      <p className="mt-6 text-center text-sm text-fg-muted">
        No account?{' '}
        <Link to="/register" className="font-medium text-accent underline-offset-4 transition-colors hover:text-fg hover:underline">
          Create one free
        </Link>
      </p>
    </>
  )
}

export default LoginPage
