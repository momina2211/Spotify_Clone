import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'

export function AppLayout() {
	const { isAuthenticated, user, logout } = useAuth()
	const navigate = useNavigate()
	return (
		<div>
			<header style={{ display: 'flex', gap: 16, padding: 12, borderBottom: '1px solid #eee' }}>
				<Link to="/">Spotify Clone</Link>
				<nav style={{ display: 'flex', gap: 12 }}>
					<NavLink to="/">Trending</NavLink>
					{isAuthenticated && <NavLink to="/upload">Upload</NavLink>}
				</nav>
				<div style={{ marginLeft: 'auto' }}>
					{isAuthenticated ? (
						<>
							<NavLink to="/profile">{user?.email}</NavLink>
							<button style={{ marginLeft: 12 }} onClick={() => { logout(); navigate('/')}}>Logout</button>
						</>
					) : (
						<>
							<NavLink to="/login">Login</NavLink>
							<NavLink style={{ marginLeft: 12 }} to="/register">Register</NavLink>
						</>
					)}
				</div>
			</header>
			<main style={{ padding: 16 }}>
				<Outlet />
			</main>
		</div>
	)
}