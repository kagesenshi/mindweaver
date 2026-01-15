import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-[#08090b] text-slate-200 flex flex-col items-center justify-center p-8">
      <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-600/20 mb-8">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" /></svg>
      </div>

      <h1 className="text-5xl font-bold tracking-tight text-white mb-2">Mindweaver React</h1>
      <p className="text-slate-500 mb-8">Frontend rewrite in progress...</p>

      <div className="bg-slate-900/40 border border-slate-800 p-8 rounded-3xl backdrop-blur-md">
        <button
          onClick={() => setCount((count) => count + 1)}
          className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-xl transition-all active:scale-95 shadow-lg shadow-blue-600/20"
        >
          Count is {count}
        </button>
      </div>

      <p className="mt-8 text-base text-slate-600 font-mono uppercase tracking-widest">
        Tailwind CSS v4 + Vite + React
      </p>
    </div>
  )
}

export default App
