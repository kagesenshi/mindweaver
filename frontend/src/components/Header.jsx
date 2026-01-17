import React, { useState } from 'react';
import Drawer from './Drawer';
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

    return (
        <header className={cn(
            "h-16 border-b backdrop-blur-md sticky top-0 z-[60] flex items-center justify-between px-8 transition-colors duration-300",
            headerBg
        )}>
            <div className="flex items-center gap-6">
                <Drawer
                    isOpen={showProjectDropdown}
                    onOpenChange={setShowProjectDropdown}
                    placement="bottom"
                    darkMode={darkMode}
                    activeBg={darkMode ? "bg-[#08090b]" : "bg-white"}
                    className="w-64"
                    trigger={
                        <div className="mw-search-box flex items-center w-full">
                            <div className={cn(
                                "p-1 rounded mr-2",
                                !selectedProject ? 'bg-blue-500/20 text-blue-400' : 'bg-indigo-500/20 text-indigo-400'
                            )}>
                                <Briefcase size={14} />
                            </div>
                            <div className="flex-1 text-left">
                                <p className={cn(
                                    "text-lg font-bold truncate",
                                    darkMode ? 'text-white' : 'text-slate-900'
                                )}>
                                    <span className="text-slate-500 font-normal mr-2">Context:</span>
                                    {selectedProject?.title || 'All Projects'}
                                </p>
                            </div>
                            <ChevronDown size={14} className={cn(
                                "text-slate-500 transition-transform duration-200 ml-2",
                                showProjectDropdown ? "rotate-180" : ""
                            )} />
                        </div>
                    }
                >
                    <div className="flex flex-col gap-1">
                        <button
                            onClick={() => { setSelectedProject(null); setShowProjectDropdown(false); }}
                            className={cn(
                                "w-full flex items-center gap-3 p-3 text-base font-bold rounded-lg transition-all",
                                darkMode ? 'text-slate-400 hover:text-white hover:bg-slate-800' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                            )}
                        >
                            <LayoutGrid size={16} /> Show All Projects
                        </button>
                        {projects.length > 0 && <div className={cn("h-px mx-2 my-1", darkMode ? "bg-slate-800" : "bg-slate-100")} />}
                        {projects.map(p => (
                            <button
                                key={p.id}
                                onClick={() => { setSelectedProject(p); setShowProjectDropdown(false); }}
                                className={cn(
                                    "w-full flex items-center gap-3 p-3 text-base rounded-lg transition-all",
                                    darkMode ? 'text-slate-400 hover:text-white hover:bg-slate-800' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                                )}
                            >
                                <div className={cn(
                                    "w-2 h-2 rounded-full",
                                    selectedProject?.id === p.id ? 'bg-blue-400 ring-2 ring-blue-400/30' : 'bg-slate-400'
                                )} />
                                {p.title}
                            </button>
                        ))}
                    </div>
                </Drawer>
            </div>

            <div className="flex items-center gap-4">
                <div className="mw-search-box py-1">
                    <Search size={14} className="text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search resources..."
                        className="bg-transparent text-lg focus:outline-none w-48"
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
