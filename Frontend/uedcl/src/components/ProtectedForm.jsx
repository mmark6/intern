import { useState } from 'react'
import { useApp } from '../context/AppContext.jsx'

export default function ProjectForm({ onClose }) {
  const { addProject } = useApp()
  const [form, setForm] = useState({ name: '', owner: '', status: 'Planning', priority: 'Medium' })

  const submit = e => {
    e.preventDefault()
    addProject(form)
    onClose?.()
  }

  return (
    <form className="form" onSubmit={submit}>
      <h3>Create Project</h3>
      <input placeholder="Project name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
      <input placeholder="Owner" value={form.owner} onChange={e => setForm({ ...form, owner: e.target.value })} required />
      <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
        <option>Planning</option>
        <option>Active</option>
        <option>Completed</option>
      </select>
      <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}>
        <option>Low</option>
        <option>Medium</option>
        <option>High</option>
      </select>
      <button className="btn primary">Save Project</button>
    </form>
  )
}