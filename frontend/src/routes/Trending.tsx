import axios from 'axios'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

type Song = {
	id: string
	title: string
	play_count: number
	likes: number
	genre?: any
	album?: any
}

export function Trending() {
	const [songs, setSongs] = useState<Song[]>([])
	const [error, setError] = useState<string | null>(null)

	useEffect(() => {
		async function load() {
			try {
				const { data } = await axios.get('/api/songs/trending')
				setSongs(data)
			} catch (err: any) {
				setError('Failed to load songs')
			}
		}
		load()
	}, [])

	return (
		<div>
			<h2>Trending</h2>
			{error && <div style={{ color: 'red' }}>{error}</div>}
			<ul>
				{songs.map(s => (
					<li key={s.id}>
						<Link to={`/songs/${s.id}`}>{s.title}</Link>
						<span style={{ marginLeft: 8 }}>▶ {s.play_count}</span>
						<span style={{ marginLeft: 8 }}>♥ {s.likes}</span>
					</li>
				))}
			</ul>
		</div>
	)
}