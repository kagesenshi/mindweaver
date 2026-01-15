import React, { useEffect, useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
    Rocket,
    Server,
    Activity,
    Cpu,
    HardDrive,
    Tag,
    Briefcase,
    Database,
    Search
} from 'lucide-react';
import { usePgSql } from '../hooks/useResources';
import { cn } from '../utils/cn';

const StatusBadge = ({ status }) => {
    const styles = {
        running: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        connected: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        warning: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
        stopped: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
        error: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
    };
    return (
        <span className={cn(
            "px-2 py-0.5 rounded-full text-[10px] font-bold border",
            styles[status] || styles.stopped
        )}>
            {(status || 'unknown').toUpperCase()}
        </span>
    );
};

const HomePage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const { platforms, loading } = usePgSql();
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');

    const filteredInstances = platforms.filter(inst => {
        const matchesProject = !selectedProject || inst.project_id === selectedProject.id;
        const matchesSearch = inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            inst.id.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && matchesSearch;
    });

    const textColor = darkMode ? "text-white" : "text-slate-900";
    const cardBg = darkMode ? "bg-slate-900/40 border-slate-800 hover:bg-slate-900/60" : "bg-white border-slate-200 shadow-sm hover:shadow-md hover:border-blue-500/50";
    const borderCol = darkMode ? "border-slate-800" : "border-slate-200";

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className={cn("text-xl font-bold", textColor)}>
                        {selectedProject ? `Stack: ${selectedProject.name}` : 'Unified Fleet'}
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">
                        Monitoring {filteredInstances.length} resources across all projects.
                    </p>
                </div>
                <button
                    onClick={() => navigate('/platform/pgsql')}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold px-4 py-2.5 rounded-lg transition-all shadow-lg shadow-blue-600/20"
                >
                    <Rocket size={14} /> NEW DEPLOYMENT
                </button>
            </div>

            <div className="flex items-center gap-4">
                <div className={cn(
                    "flex-1 relative border rounded-xl px-4 py-2 flex items-center gap-3",
                    darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
                )}>
                    <Search size={18} className="text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search within fleet..."
                        className="bg-transparent text-sm focus:outline-none w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {loading ? (
                <div className="py-20 flex flex-col items-center justify-center space-y-4">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-slate-500 text-sm font-medium">Scanning network for active resources...</p>
                </div>
            ) : filteredInstances.length === 0 ? (
                <div className="py-20 text-center border-2 border-dashed border-slate-800 rounded-[40px]">
                    <Server size={48} className="mx-auto text-slate-700 mb-4" />
                    <h3 className="text-lg font-bold text-slate-400">Quiet in the sector</h3>
                    <p className="text-slate-500 text-sm">No active resources found {selectedProject ? `for ${selectedProject.name}` : ''}.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filteredInstances.map(inst => (
                        <div
                            key={inst.id}
                            onClick={() => navigate('/platform/pgsql')} // For now, only pgsql clusters are in the list
                            className={cn(
                                "border p-5 rounded-[32px] cursor-pointer group transition-all",
                                cardBg
                            )}
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={cn(
                                        "p-2 rounded-xl text-blue-400 group-hover:scale-110 transition-transform",
                                        darkMode ? 'bg-slate-800' : 'bg-slate-100'
                                    )}>
                                        <Database size={20} />
                                    </div>
                                    <div>
                                        <h4 className={cn("text-sm font-bold", textColor)}>{inst.name}</h4>
                                        <p className="text-[9px] text-slate-500 font-mono uppercase">{inst.id}</p>
                                    </div>
                                </div>
                                <StatusBadge status="running" />
                            </div>

                            <div className={cn("grid grid-cols-2 gap-4 pt-4 border-t", borderCol)}>
                                <div className="flex items-center gap-2 text-slate-500">
                                    <Tag size={12} />
                                    <span className="text-[9px] font-bold">CloudNative PG</span>
                                </div>
                                <div className="flex items-center gap-2 text-blue-500/70">
                                    <Briefcase size={12} />
                                    <span className="text-[9px] font-bold uppercase truncate max-w-[80px]">
                                        {inst.project?.name || 'Service Component'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default HomePage;
