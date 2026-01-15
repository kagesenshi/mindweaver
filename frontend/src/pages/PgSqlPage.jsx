import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
    Plus,
    Database,
    Server,
    Settings,
    Activity,
    Terminal,
    RefreshCcw,
    Zap,
    Save,
    Lock,
    Eye,
    EyeOff,
    Copy,
    ChevronLeft,
    Search,
    CheckCircle2,
    AlertCircle
} from 'lucide-react';
import { usePgSql } from '../hooks/useResources';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';

const StatusBadge = ({ status }) => {
    const styles = {
        running: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        connected: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        warning: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
        stopped: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
        error: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
        active: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
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

const PgSqlPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const { platforms, loading, deletePlatform, updatePlatformState, getPlatformState } = usePgSql();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [selectedPlatform, setSelectedPlatform] = useState(null);
    const [platformState, setPlatformState] = useState(null);
    const [activeTab, setActiveTab] = useState('connect');
    const [showPassword, setShowPassword] = useState(false);

    const filteredPlatforms = platforms.filter(p => !selectedProject || p.project_id === selectedProject.id);

    useEffect(() => {
        if (selectedPlatform) {
            getPlatformState(selectedPlatform.id).then(setPlatformState);
        } else {
            setPlatformState(null);
        }
    }, [selectedPlatform]);

    const toggleActive = async () => {
        if (!selectedPlatform || !platformState) return;
        const newState = { active: !platformState.active };
        await updatePlatformState(selectedPlatform.id, newState);
        const updated = await getPlatformState(selectedPlatform.id);
        setPlatformState(updated);
    };

    const cardBg = darkMode ? "bg-slate-900/40 border-slate-800" : "bg-white border-slate-200 shadow-sm";
    const textColor = darkMode ? "text-white" : "text-slate-900";
    const innerCardBg = darkMode ? "bg-slate-900 border-slate-800" : "bg-white border-slate-200 shadow-sm";
    const itemBg = darkMode ? "bg-slate-950/50 border-slate-800" : "bg-slate-50 border-slate-200";

    if (selectedPlatform) {
        return (
            <div className="space-y-8 animate-in fade-in duration-500">
                <div className="flex items-end justify-between">
                    <div className="flex gap-4 items-center">
                        <div className={cn(
                            "w-16 h-16 border rounded-2xl flex items-center justify-center text-blue-400 shadow-sm",
                            darkMode ? 'bg-blue-600/10 border-blue-500/20' : 'bg-slate-50 border-slate-200'
                        )}>
                            <Database size={32} />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h3 className={cn("text-3xl font-bold", textColor)}>{selectedPlatform.name}</h3>
                                <StatusBadge status={platformState?.active ? 'active' : 'stopped'} />
                            </div>
                            <div className="flex items-center gap-4 mt-2">
                                <span className="flex items-center gap-1.5 text-xs text-slate-400">
                                    Instance ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedPlatform.id}</span>
                                </span>
                                <span className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
                                    <Terminal size={14} /> v15.4
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={toggleActive}
                            className={cn(
                                "px-6 py-2.5 rounded-xl font-bold text-xs transition-all border",
                                !platformState?.active
                                    ? 'bg-emerald-600 text-white hover:bg-emerald-500'
                                    : 'bg-rose-500/10 text-rose-500 border-rose-500/20 hover:bg-rose-500/20'
                            )}
                        >
                            {!platformState?.active ? 'POWER ON' : 'STOP SERVICE'}
                        </button>
                        <button
                            onClick={() => setSelectedPlatform(null)}
                            className={cn(
                                "px-6 py-2.5 rounded-xl font-bold text-xs border transition-all",
                                darkMode ? 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                            )}
                        >
                            BACK TO LIST
                        </button>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className={cn("flex items-center gap-4 border-b p-1", darkMode ? 'border-slate-800' : 'border-slate-200')}>
                        <button
                            onClick={() => setActiveTab('connect')}
                            className={cn(
                                "px-4 py-2 text-[10px] font-bold uppercase tracking-widest transition-all border-b-2",
                                activeTab === 'connect' ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
                            )}
                        >
                            Connection & Access
                        </button>
                        <button
                            onClick={() => setActiveTab('configure')}
                            className={cn(
                                "px-4 py-2 text-[10px] font-bold uppercase tracking-widest transition-all border-b-2",
                                activeTab === 'configure' ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
                            )}
                        >
                            Configuration
                        </button>
                    </div>

                    {activeTab === 'connect' ? (
                        <div className={cn("border rounded-2xl overflow-hidden animate-in fade-in duration-500", innerCardBg)}>
                            <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg"><Lock size={18} /></div>
                                    <h4 className={cn("text-sm font-bold uppercase tracking-wider leading-none", textColor)}>Internal Network Endpoint</h4>
                                </div>
                                <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/20 rounded-full">
                                    <CheckCircle2 size={12} className="text-emerald-500" />
                                    <span className="text-[10px] text-emerald-500 font-bold uppercase">SSL Verified</span>
                                </div>
                            </div>

                            <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-3">
                                        {[
                                            { label: 'Hostname', val: `${selectedPlatform.id}.pgsql.svc.cluster.local` },
                                            { label: 'Port', val: '5432' },
                                            { label: 'Username', val: 'mw_admin' },
                                            { label: 'Default DB', val: 'mindweaver' }
                                        ].map((item, i) => (
                                            <div key={i} className={cn("p-3 border rounded-xl group relative", itemBg)}>
                                                <p className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-1">{item.label}</p>
                                                <div className="flex items-center justify-between">
                                                    <span className={cn("text-[11px] font-mono truncate pr-4", darkMode ? 'text-slate-200' : 'text-slate-700')}>{item.val}</span>
                                                    <button className="text-slate-400 hover:text-blue-500 opacity-0 group-hover:opacity-100 transition-all"><Copy size={12} /></button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <div className={cn("p-3 border rounded-xl group relative", itemBg)}>
                                        <p className="text-[9px] text-slate-500 font-bold uppercase tracking-widest mb-1">Administrative Password</p>
                                        <div className="flex items-center justify-between">
                                            <span className={cn("text-xs font-mono", darkMode ? 'text-slate-200' : 'text-slate-700')}>
                                                {showPassword ? "__REDACTED__" : "••••••••••••••••"}
                                            </span>
                                            <div className="flex items-center gap-2">
                                                <button onClick={() => setShowPassword(!showPassword)} className="text-slate-400 hover:text-slate-600 transition-colors">
                                                    {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                                                </button>
                                                <button className="text-slate-400 hover:text-blue-500"><Copy size={14} /></button>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className={cn(
                                    "flex flex-col h-full rounded-xl border overflow-hidden",
                                    darkMode ? 'bg-slate-950/80 border-slate-800' : 'bg-slate-900 border-slate-700'
                                )}>
                                    <div className={cn("flex border-b p-1", darkMode ? 'border-slate-800' : 'border-slate-700')}>
                                        <button className="px-3 py-1.5 text-[10px] font-bold uppercase rounded-md bg-slate-700 text-white shadow-inner">bash</button>
                                        <button className="px-3 py-1.5 text-[10px] font-bold uppercase rounded-md text-slate-500 hover:text-slate-300">python</button>
                                    </div>
                                    <div className="p-4 flex-1 relative group">
                                        <pre className="text-[10px] font-mono text-blue-400 leading-relaxed overflow-x-auto whitespace-pre-wrap">
                                            psql -h {selectedPlatform.id}.pgsql.svc.cluster.local -p 5432 -U mw_admin -d mindweaver
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className={cn("border rounded-2xl overflow-hidden animate-in fade-in slide-in-from-top-4 duration-500", innerCardBg)}>
                            <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg"><Zap size={18} /></div>
                                    <h4 className={cn("text-sm font-bold uppercase tracking-wider leading-none", textColor)}>Cluster Tuning</h4>
                                </div>
                            </div>
                            <div className="p-8">
                                <DynamicForm
                                    entityPath="/platform/pgsql"
                                    mode="edit"
                                    initialData={selectedPlatform}
                                    darkMode={darkMode}
                                    onCancel={() => setActiveTab('connect')}
                                    onSuccess={() => {
                                        setActiveTab('connect');
                                    }}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-end justify-between border-b pb-6 border-slate-800/50">
                <div>
                    <h2 className={cn("text-3xl font-bold tracking-tight", textColor)}>Cloudnative PG Clusters</h2>
                    <p className="text-slate-500 mt-1">High-availability PostgreSQL managed by Kubernetes operators.</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-lg shadow-lg hover:bg-blue-500 transition-all font-sans"
                >
                    <Plus size={16} /> NEW CLUSTER
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {loading ? (
                    <div className="col-span-full py-20 flex flex-col items-center justify-center space-y-4">
                        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        <p className="text-slate-500 text-sm font-medium">Fetching clusters...</p>
                    </div>
                ) : filteredPlatforms.length === 0 ? (
                    <div className="col-span-full py-20 text-center border-2 border-dashed border-slate-800 rounded-[40px]">
                        <Database size={48} className="mx-auto text-slate-700 mb-4" />
                        <h3 className="text-lg font-bold text-slate-400">No clusters found</h3>
                        <p className="text-slate-500 text-sm">{selectedProject ? `No PostgreSQL clusters in ${selectedProject.name}.` : 'Create your first PostgreSQL cluster to get started.'}</p>
                    </div>
                ) : filteredPlatforms.map(platform => (
                    <div key={platform.id} onClick={() => setSelectedPlatform(platform)} className={cn(
                        "border p-5 rounded-[32px] cursor-pointer group transition-all",
                        cardBg
                    )}>
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-3">
                                <div className={cn(
                                    "p-2 rounded-xl text-blue-400 group-hover:scale-110 transition-transform",
                                    darkMode ? 'bg-slate-800' : 'bg-slate-100'
                                )}>
                                    <Server size={20} />
                                </div>
                                <div>
                                    <h4 className={cn("text-sm font-bold", textColor)}>{platform.name}</h4>
                                    <p className="text-[9px] text-slate-500 font-mono uppercase">{platform.id}</p>
                                </div>
                            </div>
                            <StatusBadge status="running" />
                        </div>

                        <div className={cn("grid grid-cols-2 gap-4 pt-4 border-t", darkMode ? 'border-slate-800' : 'border-slate-200')}>
                            <div className="flex items-center gap-2 text-slate-500">
                                <Activity size={12} />
                                <span className="text-[9px] font-bold">3 Instances</span>
                            </div>
                            <div className="flex items-center gap-2 text-blue-500/70">
                                <Database size={12} />
                                <span className="text-[9px] font-bold uppercase truncate max-w-[80px]">v15.4</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <Modal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                title="Provision PGSQL Cluster"
                darkMode={darkMode}
            >
                <DynamicForm
                    entityPath="/platform/pgsql"
                    mode="create"
                    darkMode={darkMode}
                    initialData={{ project_id: selectedProject?.id }}
                    onSuccess={() => {
                        setIsCreateModalOpen(false);
                    }}
                    onCancel={() => setIsCreateModalOpen(false)}
                />
            </Modal>
        </div>
    );
};

export default PgSqlPage;
