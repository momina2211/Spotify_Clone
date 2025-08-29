import axios from 'axios'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

export function SongDetail() {
	const { id } = useParams()
	const [song, setSong] = useState<any>(null)
	const [error, setError] = useState<string | null>(null)

	async function fetchSong() {
		try {
			const { data } = await axios.get(`/api/songs/${id}/`)
			setSong(data)
		} catch (err) {
			setError('Failed to load song')
		}
	}

	useEffect(() => {
		fetchSong()
	}, [id])

	const play = async () => {
		try {
			await axios.post(`/api/songs/${id}/play/`)
			await fetchSong()
		} catch {}
	}
	const like = async () => {
		try {
			await axios.post(`/api/songs/${id}/like/`)
			await fetchSong()
		} catch {}
	}
	const unlike = async () => {
		try {
			await axios.post(`/api/songs/${id}/unlike/`)
			await fetchSong()
		} catch {}
	}

	if (!song) return <div>{error || 'Loading...'}</div>

	return (
		<div>
			<h2>{song.title}</h2>
			<div>
				<button onClick={play}>Play</button>
				<button onClick={like} style={{ marginLeft: 8 }}>Like</button>
				<button onClick={unlike} style={{ marginLeft: 8 }}>Unlike</button>
			</div>
			<div style={{ marginTop: 12 }}>Plays: {song.play_count} Likes: {song.likes}</div>
			{song.audio_file && (
				<audio controls src={song.audio_file} style={{ display: 'block', marginTop: 16 }} />
			)}
		</div>
	)
}