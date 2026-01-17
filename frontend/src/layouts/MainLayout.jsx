import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import { cn } from '../utils/cn';
import { useProjects } from '../hooks/useResources';

const MainLayout = () => {
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('mindweaver-dark-mode');
        return saved !== null ? JSON.parse(saved) : true;
    });
    const [selectedProject, setSelectedProject] = useState(() => {
        const saved = localStorage.getItem('mindweaver-project');
        try {
            return saved ? JSON.parse(saved) : null;
        } catch (e) {
            console.error("Failed to parse project from local storage", e);
            return null;
        }
    });

    // Add sidebar collapse state
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
        const saved = localStorage.getItem('mindweaver-sidebar-collapsed');
        return saved !== null ? JSON.parse(saved) : false;
    });

    useEffect(() => {
        localStorage.setItem('mindweaver-dark-mode', JSON.stringify(darkMode));
        if (darkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [darkMode]);

    useEffect(() => {
        localStorage.setItem('mindweaver-sidebar-collapsed', JSON.stringify(isSidebarCollapsed));
    }, [isSidebarCollapsed]);

    const { projects, fetchProjects } = useProjects();

    const handleProjectChange = (project) => {
        setSelectedProject(project);
        if (project) {
            localStorage.setItem('mindweaver-project', JSON.stringify(project));
        } else {
            localStorage.removeItem('mindweaver-project');
        }
    };

    // Toggle function
    const toggleSidebar = () => setIsSidebarCollapsed(prev => !prev);

    return (
        <div className="mw-layout-root">
            <Sidebar
                darkMode={darkMode}
                isCollapsed={isSidebarCollapsed}
                toggleSidebar={toggleSidebar}
            />

            <div className={cn(
                "flex-1 flex flex-col transition-all duration-300 ease-in-out",
                isSidebarCollapsed ? "ml-20" : "ml-[266px]"
            )}>
                <Header
                    darkMode={darkMode}
                    setDarkMode={setDarkMode}
                    selectedProject={selectedProject}
                    setSelectedProject={handleProjectChange}
                    projects={projects}
                />

                <main className="flex-1 p-8 overflow-y-auto">
                    <Outlet key={selectedProject?.id || 'all'} context={{ darkMode, selectedProject, projects, refreshProjects: fetchProjects }} />
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
