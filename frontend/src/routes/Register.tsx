import { type FormEvent, useState } from 'react'
import { useAuth } from '../state/AuthContext'
import { useNavigate } from 'react-router-dom'

export function Register() {
	const { register } = useAuth()
	const navigate = useNavigate()
	const [email, setEmail] = useState('')
	const [password, setPassword] = useState('')
	const [error, setError] = useState<string | null>(null)

	const onSubmit = async (e: FormEvent) => {
		e.preventDefault()
		setError(null)
		try {
			await register(email, password, 1)
			navigate('/')
		} catch (err: any) {
			setError(err?.response?.data?.error || 'Registration failed')
		}
	}

	return (
		<form onSubmit={onSubmit} style={{ maxWidth: 360, display: 'grid', gap: 12 }}>
			<h2>Register</h2>
			<input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
			<input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
			<button type="submit">Create account</button>
			{error && <div style={{ color: 'red' }}>{error}</div>}
		</form>
	)
}