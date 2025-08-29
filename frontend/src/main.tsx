import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import { AppLayout } from './routes/AppLayout'
import { Login } from './routes/Login'
import { Register } from './routes/Register'
import { Profile } from './routes/Profile'
import { Trending } from './routes/Trending'
import { SongDetail } from './routes/SongDetail'
import { Upload } from './routes/Upload'
import { AuthProvider } from './state/AuthContext'

const router = createBrowserRouter([
	{
		path: '/',
		element: <AppLayout />,
		children: [
			{ index: true, element: <Trending /> },
			{ path: 'login', element: <Login /> },
			{ path: 'register', element: <Register /> },
			{ path: 'profile', element: <Profile /> },
			{ path: 'songs/:id', element: <SongDetail /> },
			{ path: 'upload', element: <Upload /> },
		],
	},
])

ReactDOM.createRoot(document.getElementById('root')!).render(
	<React.StrictMode>
		<AuthProvider>
			<RouterProvider router={router} />
		</AuthProvider>
	</React.StrictMode>,
)
