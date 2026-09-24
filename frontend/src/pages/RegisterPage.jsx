import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Alert from '../components/Alert.jsx'
import Button from '../components/Button.jsx'
import FormField from '../components/FormField.jsx'
import PasswordField from '../components/PasswordField.jsx'
import {
  BuildingIcon,
  CheckIcon,
  CodeIcon,
  FlaskIcon,
  GraduationCapIcon,
  MailIcon,
  UserIcon,
} from '../components/icons.jsx'
import { mockRegister } from '../mocks/auth.js'
import { shake } from '../utils/motion.js'
import { isValidEmail } from '../utils/validation.js'

// Roles offered at sign-up per frontend Task 70. Admin is deliberately absent.
const ROLES = [
  { value: 'student', label: 'Student', icon: GraduationCapIcon },
  { value: 'developer', label: 'Developer', icon: CodeIcon },
  { value: 'researcher', label: 'Researcher', icon: FlaskIcon },
  { value: 'organization', label: 'Organization', icon: BuildingIcon },
]

function validate({ name, email, password, role }) {
  const errors = {}
  if (!name.trim()) {
    errors.name = 'Name is required.'
  }
  if (!email.trim()) {
    errors.email = 'Email is required.'
  } else if (!isValidEmail(email)) {
    errors.email = 'Enter a valid email address.'
  }
  if (!password) {
    errors.password = 'Password is required.'
  }
  if (!role) {
    errors.role = 'Select a role.'
  }
  return errors
}

function RegisterPage() {
  const [values, setValues] = useState({ name: '', email: '', password: '', role: '' })
  const [submitted, setSubmitted] = useState(false)
  const [status, setStatus] = useState('idle') // idle | submitting | success | error
  const nameRef = useRef(null)
  const emailRef = useRef(null)
  const passwordRef = useRef(null)
  const roleRef = useRef(null)
  const roleGroupRef = useRef(null)

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
      ['name', nameRef],
      ['email', emailRef],
      ['password', passwordRef],
      ['role', roleRef],
    ].filter(([field]) => currentErrors[field])
    if (invalid.length > 0) {
      invalid.forEach(([field, ref]) =>
        shake(field === 'role' ? roleGroupRef.current : ref.current.closest('[data-field]')),
      )
      invalid[0][1].current.focus()
      return
    }

    setStatus('submitting')
    try {
      await mockRegister()
      setStatus('success')
    } catch {
      setStatus('error')
    }
  }

  const isSubmitting = status === 'submitting'

  return (
    <>
      <div className="animate-fade-up" style={{ animationDelay: '60ms' }}>
        <h1 className="text-3xl font-bold tracking-tight text-fg">Create your account</h1>
        <p className="mt-2 text-fg-muted">Join PromptShield to analyse prompts and practise safe prompting.</p>
      </div>

      <div className="mt-6 animate-fade-up" style={{ animationDelay: '120ms' }}>
        {status === 'error' && (
          <Alert variant="error" className="mb-4">
            Email already exists.
          </Alert>
        )}
        {status === 'success' && (
          <Alert variant="success" className="mb-4">
            Mock account created — nothing was saved. Real registration is wired in Task 71.{' '}
            <Link to="/login" className="font-medium text-fg underline underline-offset-4">
              Go to Sign in
            </Link>
          </Alert>
        )}

        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <FormField
            id="name"
            name="name"
            label="Full Name"
            autoComplete="name"
            icon={UserIcon}
            value={values.name}
            onChange={handleChange}
            error={errors.name}
            ref={nameRef}
          />
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
            autoComplete="new-password"
            value={values.password}
            onChange={handleChange}
            error={errors.password}
            ref={passwordRef}
          />

          <fieldset ref={roleGroupRef} aria-describedby={errors.role ? 'role-error' : undefined}>
            <legend className="mb-1.5 text-sm font-medium text-fg">I am a…</legend>
            <div className="grid grid-cols-2 gap-2">
              {ROLES.map((role, index) => (
                <label
                  key={role.value}
                  className={`group relative flex cursor-pointer items-center gap-2.5 rounded-control border bg-canvas/60 px-3 py-2 text-sm text-fg transition duration-150 ease-snappy hover:-translate-y-px hover:border-accent/50 has-checked:border-accent has-checked:bg-primary/15 has-checked:shadow-glow has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-accent ${
                    errors.role ? 'border-danger' : 'border-border'
                  }`}
                >
                  <input
                    type="radio"
                    name="role"
                    value={role.value}
                    checked={values.role === role.value}
                    onChange={handleChange}
                    aria-invalid={errors.role ? true : undefined}
                    ref={index === 0 ? roleRef : undefined}
                    className="sr-only"
                  />
                  <role.icon className="h-4.5 w-4.5 text-fg-subtle transition-colors group-hover:text-fg-muted group-has-checked:text-accent" />
                  {role.label}
                  <span
                    className="ml-auto flex h-4.5 w-4.5 scale-50 items-center justify-center rounded-full bg-accent text-canvas opacity-0 transition duration-200 ease-snappy group-has-checked:scale-100 group-has-checked:opacity-100"
                    aria-hidden="true"
                  >
                    <CheckIcon className="h-3 w-3" strokeWidth="3" />
                  </span>
                </label>
              ))}
            </div>
            {errors.role && (
              <p id="role-error" className="mt-1.5 animate-alert-in text-sm text-danger">
                {errors.role}
              </p>
            )}
          </fieldset>

          <Button type="submit" loading={isSubmitting} className="mt-1 w-full">
            {isSubmitting ? 'Creating account…' : 'Create Account'}
          </Button>
        </form>
      </div>

      <p className="mt-6 text-center text-sm text-fg-muted">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-accent underline-offset-4 transition-colors hover:text-fg hover:underline">
          Sign in
        </Link>
      </p>
    </>
  )
}

export default RegisterPage
