export default function Header() {
  return (
    <header className="bg-slate-900 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="text-2xl">📈</div>
          <h1 className="text-xl font-bold text-white">Trading Sentinel</h1>
        </div>
        <div className="text-sm text-slate-400">AI Bull/Bear Signals</div>
      </div>
    </header>
  )
}
