export default function StatCard({ label, value, accent, icon: Icon }) {
  return (
    <article className="stat-card" style={{ borderColor: `${accent}33` }}>
      <div className="stat-icon" style={{ color: accent }}>
        {Icon ? <Icon size={18} /> : null}
      </div>
      <span>{label}</span>
      <strong style={{ color: accent }}>{value}</strong>
    </article>
  )
}