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
    CheckCircle2,
    AlertCircle
} from 'lucide-react';
import { usePgSql } from '../hooks/useResources';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import ResourceCard from '../components/ResourceCard';
import PageLayout from '../components/PageLayout';

const StatusBadge = ({ status }) => {
    const styles = {
        running: 'mw-badge-success',
        connected: 'mw-badge-success',
        warning: 'mw-badge-warning',
        stopped: 'mw-badge-neutral',
        error: 'mw-badge-danger',
        active: 'mw-badge-info',
    };
    return (
        <span className={cn(styles[status] || 'mw-badge-neutral')}>
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
    const [searchTerm, setSearchTerm] = useState('');

    const filteredPlatforms = platforms.filter(p => {
        const matchesProject = !selectedProject || p.project_id === selectedProject.id;
        const matchesSearch = (p.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            String(p.id).toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && matchesSearch;
    });

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


    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this cluster?')) {
            await deletePlatform(id);
        }
    };

    if (selectedPlatform) {
        return (
            <div className="space-y-8 animate-in fade-in duration-500">
                <div className="mw-page-header">
                    <div className="flex gap-4 items-center">
                        <div className="mw-icon-box w-16 h-16 text-blue-400">
                            <Database size={32} />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{selectedPlatform.name}</h2>
                                <StatusBadge status={platformState?.active ? 'active' : 'stopped'} />
                            </div>
                            <div className="flex items-center gap-4 mt-2">
                                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                                    Instance ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedPlatform.id}</span>
                                </span>
                                <span className="flex items-center gap-1.5 text-sm text-slate-500 font-mono">
                                    <Terminal size={14} /> v15.4
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={toggleActive}
                            className={cn(
                                "px-6 py-2.5 rounded-xl font-bold text-sm transition-all border",
                                !platformState?.active
                                    ? 'bg-emerald-600 text-white hover:bg-emerald-500'
                                    : 'bg-rose-500/10 text-rose-500 border-rose-500/20 hover:bg-rose-500/20'
                            )}
                        >
                            {!platformState?.active ? 'POWER ON' : 'STOP SERVICE'}
                        </button>
                        <button
                            onClick={() => setSelectedPlatform(null)}
                            className="mw-btn-secondary px-6 py-2.5"
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
                                "px-4 py-2 text-sm font-bold uppercase tracking-widest transition-all border-b-2",
                                activeTab === 'connect' ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                            )}
                        >
                            Connection & Access
                        </button>
                        <button
                            onClick={() => setActiveTab('configure')}
                            className={cn(
                                "px-4 py-2 text-sm font-bold uppercase tracking-widest transition-all border-b-2",
                                activeTab === 'configure' ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                            )}
                        >
                            Configuration
                        </button>
                    </div>

                    {activeTab === 'connect' ? (
                        <div className="mw-panel animate-in fade-in duration-500">
                            <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg"><Lock size={18} /></div>
                                    <h4 className="text-base font-bold tracking-wider leading-none text-slate-900 dark:text-white">Internal Network Endpoint</h4>
                                </div>
                                <div className="mw-badge-success gap-2 px-3 py-1">
                                    <CheckCircle2 size={12} />
                                    SSL Verified
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
                                            <div key={i} className="p-3 border rounded-xl group relative bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800">
                                                <p className="text-sm text-slate-500 font-bold uppercase tracking-widest mb-1">{item.label}</p>
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm font-mono truncate pr-4 text-slate-700 dark:text-slate-200">{item.val}</span>
                                                    <button className="text-slate-400 hover:text-blue-500 opacity-0 group-hover:opacity-100 transition-all"><Copy size={12} /></button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <div className="p-3 border rounded-xl group relative bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800">
                                        <p className="text-sm text-slate-500 font-bold uppercase tracking-widest mb-1">Administrative Password</p>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-mono text-slate-700 dark:text-slate-200">
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
                                        <button className="px-3 py-1.5 text-sm font-bold uppercase rounded-md bg-slate-700 text-white shadow-inner">bash</button>
                                        <button className="px-3 py-1.5 text-sm font-bold uppercase rounded-md text-slate-500 hover:text-slate-300">python</button>
                                    </div>
                                    <div className="p-4 flex-1 relative group">
                                        <pre className="text-sm font-mono text-blue-400 leading-relaxed overflow-x-auto whitespace-pre-wrap">
                                            psql -h {selectedPlatform.id}.pgsql.svc.cluster.local -p 5432 -U mw_admin -d mindweaver
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="mw-panel animate-in fade-in slide-in-from-top-4 duration-500">
                            <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg"><Zap size={18} /></div>
                                    <h4 className="text-base font-bold tracking-wider leading-none text-slate-900 dark:text-white">Cluster Tuning</h4>
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
        <>
            <PageLayout
                title="Cloudnative PG Clusters"
                description="High-availability PostgreSQL managed by Kubernetes operators."
                headerActions={
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="mw-btn-primary px-4 py-2"
                    >
                        <Plus size={16} /> NEW CLUSTER
                    </button>
                }
                searchQuery={searchTerm}
                onSearchChange={(e) => setSearchTerm(e.target.value)}
                searchPlaceholder="Search PostgreSQL clusters..."
                isLoading={loading}
                isEmpty={filteredPlatforms.length === 0}
                emptyState={{
                    title: "No clusters found",
                    description: selectedProject ? `No PostgreSQL clusters in ${selectedProject.name}.` : 'Create your first PostgreSQL cluster to get started.',
                    icon: <Database size={48} className="text-slate-700" />
                }}
            >
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filteredPlatforms.map(platform => (
                        <ResourceCard
                            key={platform.id}
                            onClick={() => {
                                setSelectedPlatform(platform);
                                setActiveTab('connect');
                            }}
                            icon={<Server size={20} />}
                            title={platform.name}
                            subtitle={platform.id}
                            status="running"
                            onEdit={() => {
                                setSelectedPlatform(platform);
                                setActiveTab('configure');
                            }}
                            onDelete={() => handleDelete(platform.id)}
                        >
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center gap-2 text-slate-500">
                                    <Activity size={12} />
                                    <span className="text-sm font-bold">3 Instances</span>
                                </div>
                                <div className="flex items-center gap-2 text-blue-500/70">
                                    <Database size={12} />
                                    <span className="text-sm font-bold uppercase truncate max-w-[80px]">v15.4</span>
                                </div>
                            </div>
                        </ResourceCard>
                    ))}
                </div>
            </PageLayout>

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
        </>
    );
};

export default PgSqlPage;
