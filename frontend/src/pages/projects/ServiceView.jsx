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

            {projectState?.cluster && (
                <div className="mw-card p-8 space-y-8 animate-in slide-in-from-bottom duration-700">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="mw-icon-box text-blue-500">
                                <Activity size={24} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Cluster Fleet Health</h3>
                                <p className="text-sm text-slate-500 font-medium uppercase tracking-tight">Real-time infrastructure intelligence {projectState.cluster.k8s_version && `• K8S ${projectState.cluster.k8s_version}`}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-full">
                            <div className={`w-3 h-3 rounded-full ${projectState.cluster.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
                            <span className="text-sm font-bold uppercase tracking-tight text-slate-600 dark:text-slate-400">{projectState.cluster.status}</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {/* Resource Utilization */}
                        <div className="space-y-6 bg-slate-50/50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/50">
                            <div className="space-y-4">
                                <div className="flex justify-between items-end">
                                    <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Total CPU Allocation</p>
                                    <p className="text-sm font-bold text-slate-900 dark:text-white">{projectState.cluster.cpu_total.toFixed(1)} Cores</p>
                                </div>
                                <div className="h-2 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500 transition-all duration-1000"
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            </div>
                            <div className="space-y-4">
                                <div className="flex justify-between items-end">
                                    <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Total RAM Capacity</p>
                                    <p className="text-sm font-bold text-slate-900 dark:text-white">{projectState.cluster.ram_total.toFixed(1)} GiB</p>
                                </div>
                                <div className="h-2 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-purple-500 transition-all duration-1000"
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Node Cluster Map */}
                        <div className="space-y-4 bg-slate-50/50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/50">
                            <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4">Node Topology ({projectState.cluster.node_count})</p>
                            <div className="flex flex-wrap gap-2">
                                {Object.entries(projectState.cluster.nodes_status || {}).map(([name, status]) => (
                                    <div
                                        key={name}
                                        className={`px-3 py-1.5 rounded-lg text-xs font-bold border flex items-center gap-2 ${status === 'Ready'
                                                ? 'bg-green-500/10 border-green-500/20 text-green-500'
                                                : 'bg-red-500/10 border-red-500/20 text-red-500'
                                            }`}
                                        title={`${name}: ${status}`}
                                    >
                                        <div className={`w-1.5 h-1.5 rounded-full ${status === 'Ready' ? 'bg-green-500' : 'bg-red-500'}`} />
                                        {name.split('-').pop()}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Integration Services */}
                        <div className="space-y-4 bg-slate-50/50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/50">
                            <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4">Core Integrations</p>
                            <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${projectState.cluster.argocd_installed ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                        <Activity size={16} />
                                    </div>
                                    <span className="text-sm font-bold text-slate-700 dark:text-white">ArgoCD</span>
                                </div>
                                {projectState.cluster.argocd_installed ? (
                                    <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded uppercase">
                                        {projectState.cluster.argocd_version || "ACTIVE"}
                                    </span>
                                ) : (
                                    <span className="text-[10px] font-bold bg-slate-500/10 text-slate-400 px-2 py-0.5 rounded uppercase">MISSING</span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>

    );
};

export default ServiceView;
