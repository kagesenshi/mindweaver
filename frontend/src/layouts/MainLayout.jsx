import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import { cn } from '../utils/cn';

const MainLayout = () => {
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('mindweaver-dark-mode');
        return saved !== null ? JSON.parse(saved) : true;
    });
    const [selectedProject, setSelectedProject] = useState(null);

    useEffect(() => {
        localStorage.setItem('mindweaver-dark-mode', JSON.stringify(darkMode));
        if (darkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [darkMode]);

    // Mock projects for now
    const projects = [
        { id: 'proj-alpha', name: 'Alpha Analytics' },
        { id: 'proj-beta', name: 'Beta Logistics' },
        { id: 'proj-gamma', name: 'Internal Tools' },
    ];

    return (
        <div className="mw-layout-root">
            <Sidebar darkMode={darkMode} />

            <div className="flex-1 flex flex-col ml-64">
                <Header
                    darkMode={darkMode}
                    setDarkMode={setDarkMode}
                    selectedProject={selectedProject}
                    setSelectedProject={setSelectedProject}
                    projects={projects}
                />

                <main className="flex-1 p-8 overflow-y-auto">
                    <Outlet context={{ darkMode, selectedProject }} />
                </main>

                <footer className={cn(
                    "h-10 border-t flex items-center justify-between px-8 z-40 transition-colors",
                    darkMode ? 'bg-[#0c0e12] border-slate-800' : 'bg-white border-slate-200'
                )}>
                    <div className="flex gap-6 items-center">
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-sm text-slate-500 font-bold uppercase tracking-widest">
                                Orchestrator: Operational
                            </span>
                        </div>
                    </div>
                    <div className="text-sm font-mono text-slate-500 flex gap-4">
                        <span>Nodes: 8</span>
                        <span className={darkMode ? 'border-slate-800' : 'border-slate-200'}>|</span>
                        <span>{darkMode ? 'Dark' : 'Light'} Mode Active</span>
                    </div>
                </footer>
            </div>
        </div>
    );
};

export default MainLayout;
