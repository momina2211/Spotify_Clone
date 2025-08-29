import axios from 'axios'
import { useEffect, useState } from 'react'
import { useAuth } from '../state/AuthContext'

export function Profile() {
	const { user } = useAuth()
	const [profile, setProfile] = useState<any>(null)
	const [error, setError] = useState<string | null>(null)

	useEffect(() => {
		async function load() {
			try {
				const { data } = await axios.get('/api/profile')
				setProfile(data)
			} catch (err: any) {
				setError('Failed to load profile')
			}
		}
		load()
	}, [])

	return (
		<div>
			<h2>Profile</h2>
			<div>Email: {user?.email}</div>
			{error && <div style={{ color: 'red' }}>{error}</div>}
			<pre>{profile && JSON.stringify(profile, null, 2)}</pre>
		</div>
	)
}