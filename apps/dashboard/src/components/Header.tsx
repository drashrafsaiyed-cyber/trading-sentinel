export default function Header() {
  return (
    <header className="bg-slate-900 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="text-2xl">📈</div>
          <h1 className="text-xl font-bold text-white">Trading Sentinel</h1>
        </div>
        <nav className="flex gap-4 text-slate-300">
          <a href="/" className="hover:text-white transition">Dashboard</a>
          <a href="/watchlist" className="hover:text-white transition">Watchlist</a>
          <a href="/settings" className="hover:text-white transition">Settings</a>
        </nav>
      </div>
    </header>
  )
}
