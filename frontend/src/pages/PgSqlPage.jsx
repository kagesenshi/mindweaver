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
    AlertCircle,
    Loader2
} from 'lucide-react';
import { usePgSql } from '../hooks/useResources';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import ResourceCard from '../components/ResourceCard';
import PageLayout from '../components/PageLayout';
import ResourceConfirmModal from '../components/ResourceConfirmModal';

const StatusBadge = ({ status }) => {
    const styles = {
        running: 'mw-badge-success',
        online: 'mw-badge-success',
        connected: 'mw-badge-success',
        warning: 'mw-badge-warning',
        pending: 'mw-badge-warning',
        stopped: 'mw-badge-neutral',
        offline: 'mw-badge-neutral',
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
    const { platforms, loading, deletePlatform, updatePlatformState, getPlatformState, fetchPlatforms, refreshPlatformState } = usePgSql();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const selectedPlatform = platforms.find(p => p.id === selectedPlatformId);
    const [platformState, setPlatformState] = useState(null);
    const [activeTab, setActiveTab] = useState('connect');
    const [showPassword, setShowPassword] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [allPlatformStates, setAllPlatformStates] = useState({});
    const [isDecommissionModalOpen, setIsDecommissionModalOpen] = useState(false);

    const filteredPlatforms = platforms.filter(p => {
        const matchesProject = !selectedProject || p.project_id === selectedProject.id;
        const matchesSearch = (p.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (p.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            String(p.id).toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && matchesSearch;
    });

    useEffect(() => {
        let timer;
        const fetchStates = async () => {
            if (platforms.length === 0) return;
            const states = {};
            await Promise.all(platforms.map(async (p) => {
                try {
                    const state = await getPlatformState(p.id);
                    states[p.id] = state;
                } catch (e) {
                    console.error(`Failed to fetch state for platform ${p.id}`, e);
                }
            }));
            setAllPlatformStates(states);
        };

        if (platforms.length > 0 && !selectedPlatformId) {
            fetchStates();
            timer = setInterval(fetchStates, 5000);
        }

        return () => {
            if (timer) clearInterval(timer);
        };
    }, [platforms, selectedPlatformId, getPlatformState]);

    useEffect(() => {
        let timer;
        if (selectedPlatformId) {
            getPlatformState(selectedPlatformId).then(setPlatformState);

            // Auto-polling every 15 seconds
            timer = setInterval(() => {
                getPlatformState(selectedPlatformId).then(setPlatformState);
            }, 15000);
        } else {
            setPlatformState(null);
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [selectedPlatformId, getPlatformState]);

    const handleRefresh = async () => {
        if (!selectedPlatformId) return;
        setIsRefreshing(true);
        try {
            const updated = await refreshPlatformState(selectedPlatformId);
            setPlatformState(updated);
        } finally {
            setIsRefreshing(false);
        }
    };

    const toggleActive = async () => {
        if (!selectedPlatformId || !platformState) return;
        if (platformState.active) {
            setIsDecommissionModalOpen(true);
        } else {
            const newState = { active: true };
            await updatePlatformState(selectedPlatformId, newState);
            const updated = await getPlatformState(selectedPlatformId);
            setPlatformState(updated);
        }
    };

    const handleDecommission = async (name) => {
        if (!selectedPlatformId) return;
        const newState = { active: false };
        // We need to pass the header here. Assuming usePgSql hook handles headers if passed in some way
        // or we need to modify the apiClient. Let's assume updatePlatformState can take extra options or we just pass it in headers.
        // Actually, let's check useResources hook.
        await updatePlatformState(selectedPlatformId, newState, { 'X-RESOURCE-NAME': name });
        const updated = await getPlatformState(selectedPlatformId);
        setPlatformState(updated);
        setIsDecommissionModalOpen(false);
    };


    const handleDelete = async (id, confirmName) => {
        await deletePlatform(id, confirmName);
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
                                <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{selectedPlatform.title}</h2>
                                <StatusBadge status={platformState?.status || (platformState?.active ? 'active' : 'stopped')} />
                            </div>
                            <div className="flex items-center gap-4 mt-2">
                                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                                    Instance ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedPlatform.id}</span>
                                </span>
                                <span className="flex items-center gap-1.5 text-sm text-slate-500 font-mono">
                                    <Terminal size={14} /> {selectedPlatform.image}
                                </span>
                                {platformState?.message && (
                                    <span className="flex items-center gap-1.5 text-sm text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                                        {platformState.status === 'pending' ? (
                                            <Loader2 size={14} className="text-blue-500 animate-spin" />
                                        ) : (
                                            <Activity size={14} className="text-blue-500" />
                                        )}
                                        <span>{platformState.message}</span>
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={handleRefresh}
                            disabled={isRefreshing}
                            className="mw-btn-secondary px-6 py-2.5 flex items-center gap-2"
                        >
                            <RefreshCcw size={16} className={isRefreshing ? 'animate-spin' : ''} />
                            {isRefreshing ? 'REFRESHING...' : 'REFRESH'}
                        </button>
                        <button
                            onClick={() => setSelectedPlatformId(null)}
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
                        <button
                            onClick={() => setActiveTab('admin')}
                            className={cn(
                                "px-4 py-2 text-sm font-bold uppercase tracking-widest transition-all border-b-2",
                                activeTab === 'admin' ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                            )}
                        >
                            Administrative
                        </button>
                    </div>

                    {activeTab === 'connect' ? (
                        <div className="space-y-6 animate-in fade-in duration-500">
                            {!platformState?.active ? (
                                <PageLayout.EmptyState
                                    icon={<Zap size={40} />}
                                    title="Cluster Not Deployed"
                                    description="This PostgreSQL cluster is currently not deployed. Deploy the cluster to see connection details and access endpoints."
                                    className="p-12 bg-slate-50/50 dark:bg-slate-950/20"
                                >
                                    <button
                                        onClick={toggleActive}
                                        className="mw-btn-primary px-8 py-3 flex items-center gap-2 text-base mt-6"
                                    >
                                        <Zap size={18} /> DEPLOY CLUSTER
                                    </button>
                                </PageLayout.EmptyState>
                            ) : (
                                <>
                                    {/* External Access Section */}
                                    {platformState?.node_ports?.length > 0 && (() => {
                                        const sortedPorts = [...(platformState.node_ports || [])].sort((a, b) => {
                                            const getOrder = (name) => {
                                                if (name.endsWith('-rw-nodeport')) return 1;
                                                if (name.endsWith('-ro-nodeport')) return 2;
                                                if (name.endsWith('-r-nodeport')) return 3;
                                                return 4;
                                            };
                                            return getOrder(a.name) - getOrder(b.name);
                                        });
                                        return (
                                            <div className="mw-panel">
                                                <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                                                    <div className="flex items-center gap-3">
                                                        <div className="p-2 bg-indigo-500/10 text-indigo-500 rounded-lg"><Server size={18} /></div>
                                                        <h4 className="text-base font-bold tracking-wider leading-none text-slate-900 dark:text-white">External Network Access</h4>
                                                    </div>
                                                </div>

                                                <div className="p-6 space-y-8">
                                                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                                                        {sortedPorts.map((np, i) => {
                                                            const label = np.name.endsWith('-rw-nodeport') ? 'Read-Write' :
                                                                np.name.endsWith('-ro-nodeport') ? 'Read-Only' :
                                                                    np.name.endsWith('-r-nodeport') ? 'Read-Only (Any Nodes)' : 'PostgreSQL';
                                                            return (
                                                                <div key={i} className="p-5 border rounded-2xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 flex flex-col">
                                                                    <div className="flex items-center justify-between mb-4">
                                                                        <div>
                                                                            <p className="text-xs text-slate-500 font-bold uppercase tracking-widest leading-none mb-1">Service Type</p>
                                                                            <h5 className="text-lg font-bold text-slate-900 dark:text-white leading-none">{label}</h5>
                                                                        </div>
                                                                        <div className="px-2 py-1 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-600 border border-indigo-500/20 uppercase tracking-tighter">NodePort: {np.node_port}</div>
                                                                    </div>

                                                                    <div className="space-y-2">
                                                                        <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">Available Endpoints</p>
                                                                        {platformState.cluster_nodes?.map((node, j) => (
                                                                            <div key={j} className="flex items-center justify-between p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 group/item">
                                                                                <div className="flex flex-col min-w-0">
                                                                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight truncate">{node.hostname}</span>
                                                                                    <span className="text-sm font-mono font-bold text-slate-700 dark:text-slate-200 truncate">{node.ip}:{np.node_port}</span>
                                                                                </div>
                                                                                <button
                                                                                    onClick={() => navigator.clipboard.writeText(`${node.ip}:${np.node_port}`)}
                                                                                    className="p-2 text-slate-400 hover:text-blue-500 transition-colors shrink-0"
                                                                                    title="Copy connection string"
                                                                                >
                                                                                    <Copy size={14} />
                                                                                </button>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>

                                                    <div className="space-y-4">
                                                        <div className="flex items-start gap-4 p-4 rounded-xl bg-blue-500/5 border border-blue-500/10">
                                                            <AlertCircle className="text-blue-500 shrink-0 mt-0.5" size={20} />
                                                            <div>
                                                                <p className="text-sm font-bold text-slate-900 dark:text-white tracking-tight">External Connection Guide</p>
                                                                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                                                                    Use any of the <strong>Node IP:Port</strong> combinations listed above to connect from outside the cluster.
                                                                </p>
                                                            </div>
                                                        </div>

                                                        <div className={cn(
                                                            "flex flex-col rounded-2xl border overflow-hidden",
                                                            darkMode ? 'bg-slate-950/80 border-slate-800' : 'bg-slate-900 border-slate-700'
                                                        )}>
                                                            <div className={cn("flex border-b p-1 items-center justify-between", darkMode ? 'border-slate-800' : 'border-slate-700')}>
                                                                <div className="flex p-1 gap-1">
                                                                    <button className="px-4 py-1.5 text-xs font-bold uppercase rounded-lg bg-slate-700 text-white shadow-inner">bash</button>
                                                                    <button className="px-4 py-1.5 text-xs font-bold uppercase rounded-lg text-slate-500 hover:text-slate-300">python</button>
                                                                </div>
                                                                <div className="px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">CLI Example</div>
                                                            </div>
                                                            <div className="p-6 relative group">
                                                                <pre className="text-sm font-mono text-blue-400 leading-relaxed overflow-x-auto whitespace-pre-wrap">
                                                                    psql -h {platformState.cluster_nodes?.[0]?.ip || '[NODE_IP]'} -p {sortedPorts?.[0]?.node_port || '[PORT]'} -U {platformState?.db_user || 'pending'} -d {platformState?.db_name || 'pending'}
                                                                </pre>
                                                                <button
                                                                    onClick={() => navigator.clipboard.writeText(`psql -h ${platformState.cluster_nodes?.[0]?.ip || '[NODE_IP]'} -p ${sortedPorts?.[0]?.node_port || '[PORT]'} -U ${platformState?.db_user || 'pending'} -d ${platformState?.db_name || 'pending'}`)}
                                                                    className="absolute top-4 right-4 p-2 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
                                                                >
                                                                    <Copy size={16} />
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })()}

                                    {/* Cluster Credentials Section */}
                                    {platformState?.db_user && platformState?.db_pass && (
                                        <div className="mw-panel">
                                            <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg"><Lock size={18} /></div>
                                                    <h4 className="text-base font-bold tracking-wider leading-none text-slate-900 dark:text-white">Cluster Credentials</h4>
                                                </div>
                                            </div>

                                            <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                                                <div className="p-3 border rounded-xl group relative bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800">
                                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Username</p>
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-mono truncate pr-4 text-slate-700 dark:text-slate-200">{platformState?.db_user || 'pending'}</span>
                                                        <button onClick={() => navigator.clipboard.writeText(platformState?.db_user || '')} className="text-slate-400 hover:text-blue-500 opacity-0 group-hover:opacity-100 transition-all"><Copy size={12} /></button>
                                                    </div>
                                                </div>

                                                <div className="p-3 border rounded-xl group relative bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800">
                                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Password</p>
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-mono text-slate-700 dark:text-slate-200">
                                                            {showPassword ? (platformState?.db_pass || "pending") : "••••••••••••••••"}
                                                        </span>
                                                        <div className="flex items-center gap-2">
                                                            <button onClick={() => setShowPassword(!showPassword)} className="text-slate-400 hover:text-slate-600 transition-colors">
                                                                {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                                                            </button>
                                                            <button onClick={() => navigator.clipboard.writeText(platformState?.db_pass || "")} className="text-slate-400 hover:text-blue-500"><Copy size={14} /></button>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="p-3 border rounded-xl group relative bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800">
                                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Database</p>
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-mono truncate pr-4 text-slate-700 dark:text-slate-200">{platformState?.db_name || 'pending'}</span>
                                                        <button onClick={() => navigator.clipboard.writeText(platformState?.db_name || '')} className="text-slate-400 hover:text-blue-500 opacity-0 group-hover:opacity-100 transition-all"><Copy size={12} /></button>
                                                    </div>
                                                </div>
                                            </div>

                                            {platformState?.db_ca_crt && (
                                                <div className="px-6 pb-6 animate-in slide-in-from-top-2 duration-300">
                                                    <div className="p-4 border rounded-xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">CA Certificate</p>
                                                            <button
                                                                onClick={() => navigator.clipboard.writeText(platformState.db_ca_crt)}
                                                                className="text-xs font-bold text-blue-500 hover:text-blue-400 flex items-center gap-1.5 transition-colors"
                                                            >
                                                                <Copy size={12} /> COPY CERTIFICATE
                                                            </button>
                                                        </div>
                                                        <div className="bg-slate-900 rounded-lg p-3 relative group text-emerald-400/90">
                                                            <pre className="text-[10px] font-mono leading-tight overflow-x-auto max-h-[120px] scrollbar-thin scrollbar-thumb-slate-700">
                                                                {platformState.db_ca_crt}
                                                            </pre>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    ) : activeTab === 'configure' ? (
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
                                    onSuccess={async () => {
                                        await new Promise(resolve => setTimeout(resolve, 500));
                                        await fetchPlatforms();
                                        setActiveTab('connect');
                                    }}
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6 animate-in fade-in slide-in-from-top-4 duration-500">
                            <div className="mw-panel overflow-hidden border-rose-500/20">
                                <div className="p-4 border-b bg-rose-500/5 border-rose-500/10 flex items-center gap-3">
                                    <AlertCircle className="text-rose-500" size={20} />
                                    <h4 className="text-base font-bold tracking-wider text-rose-500 uppercase">Danger Zone</h4>
                                </div>
                                <div className="p-8 space-y-6">
                                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                                        <div className="space-y-1">
                                            <h5 className="text-lg font-bold text-slate-900 dark:text-white">Decommission Cluster</h5>
                                            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl">
                                                Decommissioning this cluster will permanently delete all associated Kubernetes resources and database data.
                                                <strong className="text-rose-500 ml-1">This action cannot be undone.</strong>
                                            </p>
                                        </div>
                                        <button
                                            onClick={toggleActive}
                                            disabled={!platformState?.active}
                                            className={cn(
                                                "px-8 py-3 rounded-xl font-bold text-sm transition-all border shrink-0",
                                                platformState?.active
                                                    ? "bg-rose-500 text-white hover:bg-rose-600 border-rose-600 shadow-lg shadow-rose-500/20"
                                                    : "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
                                            )}
                                        >
                                            DECOMMISSION CLUSTER
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                {isDecommissionModalOpen && (
                    <ResourceConfirmModal
                        isOpen={isDecommissionModalOpen}
                        onClose={() => setIsDecommissionModalOpen(false)}
                        onConfirm={handleDecommission}
                        resourceName={selectedPlatform?.name}
                        darkMode={darkMode}
                        title="Confirm Decommissioning"
                        message="Decommissioning this cluster will permanently delete all associated Kubernetes resources and database data."
                        confirmText="DECOMMISSION"
                        icon={Zap}
                        variant="danger"
                    />
                )}
            </div >
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
                                setSelectedPlatformId(platform.id);
                                setActiveTab('connect');
                            }}
                            icon={<Server size={20} />}
                            title={platform.title}
                            subtitle={platform.id}
                            status={allPlatformStates[platform.id]?.status || (allPlatformStates[platform.id]?.active ? 'active' : 'stopped')}
                            onEdit={() => {
                                setSelectedPlatformId(platform.id);
                                setActiveTab('configure');
                            }}
                            resourceName={platform.name}
                            darkMode={darkMode}
                            onDelete={(name) => handleDelete(platform.id, name)}
                            footer={allPlatformStates[platform.id]?.message && (
                                <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 dark:bg-slate-800/50 px-2 py-1 rounded-lg truncate">
                                    {allPlatformStates[platform.id]?.status === 'pending' ? (
                                        <Loader2 size={12} className="text-blue-500 shrink-0 animate-spin" />
                                    ) : (
                                        <Activity size={12} className="text-blue-500 shrink-0" />
                                    )}
                                    <span className="truncate">{allPlatformStates[platform.id].message}</span>
                                </div>
                            )}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-slate-500">
                                    <Activity size={12} />
                                    <span className="text-base font-bold">{platform.instances} Instances</span>
                                </div>
                                <div className="flex items-center gap-2 text-blue-500/70">
                                    <Database size={12} />
                                    <span className="text-base font-bold uppercase truncate max-w-[120px]">{platform.image}</span>
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
                    initialData={React.useMemo(() => ({ project_id: selectedProject?.id }), [selectedProject?.id])}
                    onSuccess={async () => {
                        await new Promise(resolve => setTimeout(resolve, 500));
                        await fetchPlatforms();
                        setIsCreateModalOpen(false);
                    }}
                    onCancel={() => setIsCreateModalOpen(false)}
                />
            </Modal>


        </>
    );
};

export default PgSqlPage;
