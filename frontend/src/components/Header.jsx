import React, { useState } from 'react';
import {
    Search,
    Sun,
    Moon,
    Briefcase,
    ChevronDown,
    LayoutGrid
} from 'lucide-react';
import { cn } from '../utils/cn';

const Header = ({ darkMode, setDarkMode, selectedProject, setSelectedProject, projects = [] }) => {
    const [showProjectDropdown, setShowProjectDropdown] = useState(false);

    const headerBg = darkMode ? "bg-[#08090b]/80 border-slate-800" : "bg-white/90 border-slate-200";
    const borderCol = darkMode ? "border-slate-800" : "border-slate-200";

    return (
        <header className={cn(
            "h-16 border-b backdrop-blur-md sticky top-0 z-[60] flex items-center justify-between px-8 transition-colors duration-300",
            headerBg
        )}>
            <div className="flex items-center gap-6">
                <div className="relative">
                    <button
                        onClick={() => setShowProjectDropdown(!showProjectDropdown)}
                        className={cn(
                            "flex items-center gap-3 border rounded-lg px-3 py-1.5 transition-all min-w-[200px]",
                            darkMode ? 'bg-slate-900 border-slate-800 hover:border-slate-700' : 'bg-white border-slate-200 hover:border-slate-300'
                        )}
                    >
                        <div className={cn(
                            "p-1 rounded",
                            !selectedProject ? 'bg-blue-500/20 text-blue-400' : 'bg-indigo-500/20 text-indigo-400'
                        )}>
                            <Briefcase size={14} />
                        </div>
                        <div className="flex-1 text-left">
                            <p className="text-[9px] text-slate-500 uppercase font-bold tracking-tighter leading-none">Context</p>
                            <p className={cn(
                                "text-xs font-bold truncate",
                                darkMode ? 'text-white' : 'text-slate-900'
                            )}>
                                {selectedProject?.name || 'All Projects'}
                            </p>
                        </div>
                        <ChevronDown size={14} className="text-slate-500" />
                    </button>

                    {showProjectDropdown && (
                        <>
                            <div
                                className="fixed inset-0 z-10"
                                onClick={() => setShowProjectDropdown(false)}
                            />
                            <div className={cn(
                                "absolute top-full left-0 mt-2 w-64 border rounded-xl shadow-2xl z-20 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200",
                                darkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
                            )}>
                                <button
                                    onClick={() => { setSelectedProject(null); setShowProjectDropdown(false); }}
                                    className={cn(
                                        "w-full flex items-center gap-3 p-3 text-xs font-bold border-b transition-all",
                                        darkMode ? 'text-slate-400 hover:bg-slate-800 border-slate-800' : 'text-slate-600 hover:bg-slate-50 border-slate-100'
                                    )}
                                >
                                    <LayoutGrid size={14} /> Show All Projects
                                </button>
                                {projects.map(p => (
                                    <button
                                        key={p.id}
                                        onClick={() => { setSelectedProject(p); setShowProjectDropdown(false); }}
                                        className={cn(
                                            "w-full flex items-center gap-3 p-3 text-xs transition-all",
                                            darkMode ? 'text-slate-400 hover:bg-slate-800' : 'text-slate-600 hover:bg-slate-50'
                                        )}
                                    >
                                        <div className={cn(
                                            "w-1.5 h-1.5 rounded-full",
                                            selectedProject?.id === p.id ? 'bg-blue-400' : 'bg-slate-400'
                                        )} />
                                        {p.name}
                                    </button>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            </div>

            <div className="flex items-center gap-4">
                <div className={cn(
                    "relative border rounded-lg px-3 py-1 flex items-center gap-2",
                    darkMode ? 'bg-slate-900 border-slate-800' : 'bg-slate-100 border-slate-200'
                )}>
                    <Search size={14} className="text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search resources..."
                        className="bg-transparent text-xs focus:outline-none w-48"
                    />
                </div>
                <button
                    onClick={() => setDarkMode(!darkMode)}
                    className={cn(
                        "p-2 rounded-lg border transition-all",
                        darkMode ? 'bg-slate-900 border-slate-800 text-amber-400 hover:bg-slate-800' : 'bg-white border-slate-200 text-blue-600 hover:bg-slate-50 shadow-sm'
                    )}
                >
                    {darkMode ? <Sun size={18} /> : <Moon size={18} />}
                </button>
            </div>
        </header>
    );
};

export default Header;
