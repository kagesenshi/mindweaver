import React, { useState, useEffect } from 'react';
import {
    Briefcase, Database, Server, Activity, ArrowLeft, Monitor
} from 'lucide-react';

const ServiceView = ({
    context,
    selectedProjectId,
    selectedProject,
    onBack,
    projectsHook
}) => {
    const { getProjectState } = projectsHook;
    const [projectState, setProjectState] = useState(null);
    const { darkMode } = context;

    useEffect(() => {
        let timer;
        if (selectedProjectId) {
            getProjectState(selectedProjectId).then(setProjectState);

            timer = setInterval(() => {
                getProjectState(selectedProjectId).then(setProjectState);
            }, 10000);
        } else {
            setProjectState(null);
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [selectedProjectId, getProjectState]);

    const resourceCards = [
        {
            name: "PostgreSQL",
            icon: Database,
            count: projectState?.pgsql || 0,
            color: "text-blue-500",
            bg: "bg-blue-500/10"
        },
        {
            name: "Trino",
            icon: Server,
            count: projectState?.trino || 0,
            color: "text-purple-500",
            bg: "bg-purple-500/10"
        },
        {
            name: "Spark",
            icon: Activity,
            count: projectState?.spark || 0,
            color: "text-orange-500",
            bg: "bg-orange-500/10"
        },
        {
            name: "Airflow",
            icon: Activity,
            count: projectState?.airflow || 0,
            color: "text-teal-500",
            bg: "bg-teal-500/10"
        }
    ];

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="mw-page-header">
                <div className="flex gap-4 items-center">
                    <button
                        onClick={onBack}
                        className="p-3 text-slate-400 hover:text-slate-900 dark:hover:text-white transition-all bg-slate-100 dark:bg-slate-800 rounded-xl"
                    >
                        <ArrowLeft size={24} />
                    </button>
                    <div className="mw-icon-box w-16 h-16 text-indigo-400">
                        <Monitor size={32} />
                    </div>
                    <div>
                        <div className="flex items-center gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{selectedProject.title} Fleet Overview</h2>
                        </div>
                        <div className="flex items-center gap-4 mt-2">
                            <span className="flex items-center gap-1.5 text-sm text-slate-400">
                                Project ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedProject.id}</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                {resourceCards.map((card, i) => {
                    const Icon = card.icon;
                    return (
                        <div key={i} className="mw-card p-6 flex flex-col gap-4">
                            <div className="flex items-center gap-4">
                                <div className={`p-4 rounded-xl ${card.bg} ${card.color}`}>
                                    <Icon size={24} />
                                </div>
                                <h3 className="text-xl font-bold text-slate-900 dark:text-white uppercase tracking-wider">{card.name}</h3>
                            </div>
                            <div className="mt-2 text-center bg-slate-50 dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                                <p className="text-4xl font-bold text-slate-900 dark:text-white mb-1">{card.count}</p>
                                <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Instances Deployed</p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default ServiceView;
