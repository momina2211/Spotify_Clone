import axios from 'axios'
import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export function Upload() {
	const navigate = useNavigate()
	const [title, setTitle] = useState('')
	const [duration, setDuration] = useState<number>(0)
	const [releaseDate, setReleaseDate] = useState('')
	const [genre, setGenre] = useState('')
	const [albumTitle, setAlbumTitle] = useState('')
	const [audioFile, setAudioFile] = useState<File | null>(null)
	const [error, setError] = useState<string | null>(null)

	const onSubmit = async (e: FormEvent) => {
		e.preventDefault()
		setError(null)
		try {
			const form = new FormData()
			form.append('title', title)
			form.append('duration', String(duration))
			form.append('release_date', releaseDate)
			form.append('genre', genre)
			if (albumTitle) form.append('album_title', albumTitle)
			if (audioFile) form.append('audio_file', audioFile)
			const { data } = await axios.post('/api/songs/', form, { headers: { 'Content-Type': 'multipart/form-data' } })
			navigate(`/songs/${data.id}`)
		} catch (err: any) {
			setError(err?.response?.data?.error || 'Upload failed')
		}
	}

	return (
		<form onSubmit={onSubmit} style={{ maxWidth: 480, display: 'grid', gap: 12 }}>
			<h2>Upload Song</h2>
			<input placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} />
			<input placeholder="Duration (seconds)" type="number" value={duration} onChange={e => setDuration(Number(e.target.value))} />
			<input placeholder="Release Date" type="date" value={releaseDate} onChange={e => setReleaseDate(e.target.value)} />
			<input placeholder="Genre" value={genre} onChange={e => setGenre(e.target.value)} />
			<input placeholder="Album (optional)" value={albumTitle} onChange={e => setAlbumTitle(e.target.value)} />
			<input type="file" accept="audio/*" onChange={e => setAudioFile(e.target.files?.[0] || null)} />
			<button type="submit">Upload</button>
			{error && <div style={{ color: 'red' }}>{error}</div>}
		</form>
	)
}