import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import axios from 'axios'

export type AuthUser = {
	id: string
	email: string
}

type AuthContextShape = {
	token: string | null
	user: AuthUser | null
	isAuthenticated: boolean
	login: (email: string, password: string) => Promise<void>
	register: (email: string, password: string, role?: number) => Promise<void>
	logout: () => void
}

const AuthContext = createContext<AuthContextShape | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
	const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
	const [user, setUser] = useState<AuthUser | null>(() => {
		const raw = localStorage.getItem('user')
		return raw ? (JSON.parse(raw) as AuthUser) : null
	})

	useEffect(() => {
		if (token) {
			axios.defaults.headers.common['Authorization'] = `Token ${token}`
			localStorage.setItem('token', token)
		} else {
			delete axios.defaults.headers.common['Authorization']
			localStorage.removeItem('token')
		}
	}, [token])

	useEffect(() => {
		if (user) localStorage.setItem('user', JSON.stringify(user))
		else localStorage.removeItem('user')
	}, [user])

	const isAuthenticated = !!token

	const login = async (email: string, password: string) => {
		const { data } = await axios.post('/api/login', { email, password })
		setToken(data.token)
		setUser(data.user)
	}

	const register = async (email: string, password: string, role = 1) => {
		const { data } = await axios.post('/api/users', { email, password, role })
		setToken(data.token)
		setUser(data.user)
	}

	const logout = () => {
		setToken(null)
		setUser(null)
	}

	const value = useMemo(
		() => ({ token, user, isAuthenticated, login, register, logout }),
		[token, user, isAuthenticated],
	)

	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
	const ctx = useContext(AuthContext)
	if (!ctx) throw new Error('useAuth must be used within AuthProvider')
	return ctx
}