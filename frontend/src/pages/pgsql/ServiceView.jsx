import React, { useState, useEffect } from 'react';
import { Database, Server, Lock, Eye, EyeOff, Copy, AlertCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    pgsql
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms, fetchActions, executeAction } = pgsql;
    const [platformState, setPlatformState] = useState(null);
    const [showPassword, setShowPassword] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [availableActions, setAvailableActions] = useState([]);
    const [isExecutingAction, setIsExecutingAction] = useState(null);

    const { showSuccess, showError } = useNotification();

    useEffect(() => {
        let timer;
        if (selectedPlatformId) {
            getPlatformState(selectedPlatformId).then(setPlatformState);
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

    useEffect(() => {
        if (selectedPlatformId && platformState?.active) {
            fetchActions(selectedPlatformId).then(setAvailableActions);
        } else {
            setAvailableActions([]);
        }
    }, [selectedPlatformId, platformState?.active, fetchActions]);

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
        setPlatformState({ ...platformState, active: true, status: 'pending', message: 'Triggering deployment...' });
        try {
            const response = await updatePlatformState(selectedPlatformId, { active: true });
            if (response) {
                setPlatformState(response);
            }
            await handleRefresh();
        } catch (err) {
            showError(`Failed to trigger deployment: ${err.message}`);
            const original = await getPlatformState(selectedPlatformId);
            setPlatformState(original);
        }
    };

    const handleDecommission = async (name) => {
        if (!selectedPlatformId) return;
        setPlatformState({ ...platformState, active: false, status: 'offline', message: 'Decommissioning...' });
        try {
            const response = await updatePlatformState(selectedPlatformId, { active: false }, { 'X-RESOURCE-NAME': name });
            if (response) {
                setPlatformState(response);
            }
            await handleRefresh();
        } catch (err) {
            showError(`Failed to decommission cluster: ${err.message}`);
            const original = await getPlatformState(selectedPlatformId);
            setPlatformState(original);
        }
    };

    const handleExecuteAction = async (actionName) => {
        if (!selectedPlatformId) return;
        setIsExecutingAction(actionName);
        try {
            await executeAction(selectedPlatformId, actionName);
            showSuccess(`Action ${actionName} triggered successfully`);
            await handleRefresh();
        } catch (err) {
            showError(`Failed to trigger action ${actionName}: ${err.message}`);
        } finally {
            setIsExecutingAction(null);
        }
    };

    const renderConnectTab = () => {
        const sortedPorts = platformState?.node_ports ? [...platformState.node_ports].sort((a, b) => {
            const getOrder = (name) => {
                if (name.endsWith('-rw-nodeport')) return 1;
                if (name.endsWith('-ro-nodeport')) return 2;
                if (name.endsWith('-r-nodeport')) return 3;
                return 4;
            };
            return getOrder(a.name) - getOrder(b.name);
        }) : [];

        return (
            <>
                {platformState?.extra_data?.namespace && (
                    <div className="mw-panel">
                        <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-emerald-500/10 text-emerald-500 rounded-lg"><Server size={18} /></div>
                                <h4 className="text-base font-bold tracking-wider leading-none text-slate-900 dark:text-white">Internal Network Access</h4>
                            </div>
                        </div>
                        <div className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                                {[
                                    { label: 'Read-Write', suffix: '-rw' },
                                    { label: 'Read-Only', suffix: '-ro' },
                                    { label: 'Read-Only (Any Nodes)', suffix: '-r' }
                                ].map((eps) => {
                                    const hostname = `${selectedPlatform.name}${eps.suffix}.${platformState.extra_data.namespace}.svc.cluster.local`;
                                    return (
                                        <div key={eps.suffix} className="p-5 border rounded-2xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 flex flex-col group/item relative">
                                            <div className="flex items-center justify-between mb-2">
                                                <div>
                                                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest leading-none mb-1">Service Type</p>
                                                    <h5 className="text-lg font-bold text-slate-900 dark:text-white leading-none">{eps.label}</h5>
                                                </div>
                                            </div>
                                            <div className="mt-2 p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                                                <code className="text-xs font-mono text-emerald-600 dark:text-emerald-400 truncate px-1">{hostname}:5432</code>
                                                <button
                                                    onClick={() => navigator.clipboard.writeText(`${hostname}:5432`)}
                                                    className="p-1 text-slate-400 hover:text-emerald-500 transition-colors shrink-0"
                                                    title="Copy internal endpoint"
                                                >
                                                    <Copy size={14} />
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {sortedPorts.length > 0 && (
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
                                                    <div key={j} className="flex flex-col gap-1 p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 group/item">
                                                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight truncate px-1">{node.hostname}</span>
                                                        {node.ipv4 && (
                                                            <div className="flex items-center justify-between">
                                                                <span className="text-sm font-mono font-bold text-slate-700 dark:text-slate-200 truncate px-1">{node.ipv4}:{np.node_port}</span>
                                                                <button
                                                                    onClick={() => navigator.clipboard.writeText(`${node.ipv4}:${np.node_port}`)}
                                                                    className="p-1 text-slate-400 hover:text-blue-500 transition-colors shrink-0"
                                                                    title="Copy IPv4 connection string"
                                                                >
                                                                    <Copy size={14} />
                                                                </button>
                                                            </div>
                                                        )}
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
                                            psql "host={platformState.cluster_nodes?.[0]?.ipv4 || '[NODE_IP]'} port={sortedPorts?.[0]?.node_port || '[PORT]'} user={platformState?.db_user || 'pending'} dbname={platformState?.db_name || 'pending'} sslmode=verify-full sslrootcert=ca.crt"
                                        </pre>
                                        <button
                                            onClick={() => navigator.clipboard.writeText(`psql "host=${platformState.cluster_nodes?.[0]?.ipv4 || '[NODE_IP]'} port=${sortedPorts?.[0]?.node_port || '[PORT]'} user=${platformState?.db_user || 'pending'} dbname=${platformState?.db_name || 'pending'} sslmode=verify-full sslrootcert=ca.crt"`)}
                                            className="absolute top-4 right-4 p-2 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
                                        >
                                            <Copy size={16} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

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
        );
    };

    return (
        <PlatformServiceView
            darkMode={darkMode}
            selectedPlatformId={selectedPlatformId}
            selectedPlatform={selectedPlatform}
            platformState={platformState}
            onBack={onBack}
            initialTab={initialTab}
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
            onToggleActive={toggleActive}
            onDecommission={handleDecommission}
            availableActions={availableActions}
            isExecutingAction={isExecutingAction}
            onExecuteAction={handleExecuteAction}
            icon={Database}
            iconClassName="text-blue-400"
            entityPath="/platform/pgsql"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Decommissioning this cluster will permanently delete all associated Kubernetes resources and database data. This action cannot be undone."
            notDeployedTitle="Cluster Not Deployed"
            notDeployedDescription="This PostgreSQL cluster is currently not deployed. Deploy the cluster to see connection details and access endpoints."
            deployButtonText="DEPLOY CLUSTER"
        />
    );
};

export default ServiceView;
