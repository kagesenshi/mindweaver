import React, { useState, useEffect } from 'react';
import {
    Activity, Monitor, RefreshCw
} from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';

const ServiceView = ({
    selectedClusterId,
    selectedCluster,
    onBack,
    clustersHook
}) => {
    const { getClusterState, refreshClusterState } = clustersHook;
    const [clusterState, setClusterState] = useState(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [installingActions, setInstallingActions] = useState({});
    const { showSuccess, showError } = useNotification();

    useEffect(() => {
        let timer;
        if (selectedClusterId && getClusterState) {
            getClusterState(selectedClusterId).then(setClusterState);

            timer = setInterval(() => {
                getClusterState(selectedClusterId).then(setClusterState);
            }, 10000);
        } else {
            Promise.resolve().then(() => setClusterState(null));
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [selectedClusterId, getClusterState]);

    const handleRefresh = async () => {
        if (!refreshClusterState) return;
        setIsRefreshing(true);
        try {
            const newState = await refreshClusterState(selectedClusterId);
            setClusterState(newState);
            showSuccess("Cluster state refreshed");
        } catch (e) {
            console.error(e);
            showError("Failed to refresh cluster state");
        } finally {
            setIsRefreshing(false);
        }
    };

    const handleInstallAction = async (actionId) => {
        setInstallingActions(prev => ({ ...prev, [actionId]: true }));
        try {
            await clustersHook.executeAction(selectedClusterId, actionId);
            showSuccess("Installation triggered");
        } catch (e) {
            console.error(e);
            showError("Failed to trigger installation");
        } finally {
            // We don't necessarily clear it immediately because the poller will 
            // update the 'installed' status in a few seconds, which will remove the button.
            // But we clear it just in case of error or if it takes long.
            setTimeout(() => {
                setInstallingActions(prev => ({ ...prev, [actionId]: false }));
            }, 5000);
        }
    };

    if (!clusterState) {
        return (
            <div className="space-y-8 animate-in fade-in duration-500">
                <div className="mw-page-header">
                    <div className="flex gap-4 items-center">
                        <div className="mw-icon-box w-16 h-16 text-slate-400">
                            <Monitor size={32} />
                        </div>
                        <div>
                            <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">Loading Cluster State...</h2>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={onBack}
                            className="mw-btn-secondary px-6 py-2.5"
                        >
                            BACK TO LIST
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="mw-page-header">
                <div className="flex gap-4 items-center">
                    <div className="mw-icon-box w-16 h-16 text-indigo-400">
                        <Monitor size={32} />
                    </div>
                    <div>
                        <div className="flex items-center gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{selectedCluster.title} Health</h2>
                        </div>
                        <div className="flex items-center gap-4 mt-2">
                            <span className="flex items-center gap-1.5 text-sm text-slate-400">
                                Cluster ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedCluster.id}</span>
                            </span>
                        </div>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                        className="mw-btn-secondary px-6 py-2.5 flex items-center gap-2"
                    >
                        <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
                        {isRefreshing ? 'REFRESHING...' : 'REFRESH'}
                    </button>
                    <button
                        onClick={onBack}
                        className="mw-btn-secondary px-6 py-2.5"
                    >
                        BACK TO LIST
                    </button>
                </div>
            </div>

            <div className="mw-card p-8 space-y-8 animate-in slide-in-from-bottom duration-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="mw-icon-box text-blue-500">
                            <Activity size={24} />
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Cluster Health</h3>
                            <p className="text-sm text-slate-500 font-medium uppercase tracking-tight">Real-time infrastructure intelligence {clusterState.k8s_version && `• K8S ${clusterState.k8s_version}`}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-full">
                        <div className={`w-3 h-3 rounded-full ${clusterState.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="text-sm font-bold uppercase tracking-tight text-slate-600 dark:text-slate-400">{clusterState.status}</span>
                    </div>
                </div>

                {clusterState.message && clusterState.status === 'error' && (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-500 rounded-xl text-sm font-mono whitespace-pre-wrap">
                        {clusterState.message}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Resource Utilization */}
                    <div className="space-y-6 bg-slate-50/50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/50">
                        <div className="space-y-4">
                            <div className="flex justify-between items-end">
                                <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Total CPU Allocation</p>
                                <p className="text-sm font-bold text-slate-900 dark:text-white">{(clusterState.cpu_total || 0).toFixed(1)} Cores</p>
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
                                <p className="text-sm font-bold text-slate-900 dark:text-white">{(clusterState.ram_total || 0).toFixed(1)} GiB</p>
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
                        <p className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4">Node Topology ({clusterState.node_count || 0})</p>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(clusterState.nodes_status || {}).map(([name, status]) => (
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
                        
                        {/* ArgoCD */}
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${clusterState.argocd_installed ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                    <Activity size={16} />
                                </div>
                                <span className="text-sm font-bold text-slate-700 dark:text-white">ArgoCD</span>
                            </div>
                            {clusterState.argocd_installed ? (
                                <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                                    {clusterState.argocd_version || "ACTIVE"}
                                </span>
                            ) : (
                                <button 
                                    onClick={() => handleInstallAction('install_argocd')}
                                    disabled={installingActions['install_argocd']}
                                    className="mw-btn-primary py-1 px-3 text-[10px] flex items-center gap-2"
                                >
                                    {installingActions['install_argocd'] && <RefreshCw size={10} className="animate-spin" />}
                                    {installingActions['install_argocd'] ? 'INSTALLING' : 'INSTALL'}
                                </button>
                            )}
                        </div>

                        {/* Cert Manager */}
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${clusterState.cert_manager_installed ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                    <Activity size={16} />
                                </div>
                                <span className="text-sm font-bold text-slate-700 dark:text-white">Cert Manager</span>
                            </div>
                            {clusterState.cert_manager_installed ? (
                                <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                                    {clusterState.cert_manager_version || "ACTIVE"}
                                </span>
                            ) : (
                                <button 
                                    onClick={() => handleInstallAction('install_cert_manager')}
                                    disabled={installingActions['install_cert_manager']}
                                    className="mw-btn-primary py-1 px-3 text-[10px] flex items-center gap-2"
                                >
                                    {installingActions['install_cert_manager'] && <RefreshCw size={10} className="animate-spin" />}
                                    {installingActions['install_cert_manager'] ? 'INSTALLING' : 'INSTALL'}
                                </button>
                            )}
                        </div>

                        {/* CNPG Operator */}
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${clusterState.cnpg_installed ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                    <Activity size={16} />
                                </div>
                                <span className="text-sm font-bold text-slate-700 dark:text-white">CNPG Operator</span>
                            </div>
                            {clusterState.cnpg_installed ? (
                                <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                                    {clusterState.cnpg_version || "ACTIVE"}
                                </span>
                            ) : (
                                <button 
                                    id="install-cnpg-operator-btn"
                                    onClick={() => handleInstallAction('install_cnpg_operator')}
                                    disabled={installingActions['install_cnpg_operator']}
                                    className="mw-btn-primary py-1 px-3 text-[10px] flex items-center gap-2"
                                >
                                    {installingActions['install_cnpg_operator'] && <RefreshCw size={10} className="animate-spin" />}
                                    {installingActions['install_cnpg_operator'] ? 'INSTALLING' : 'INSTALL'}
                                </button>
                            )}
                        </div>

                        {/* Self-Signed ClusterIssuer */}
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${clusterState.cluster_issuer_installed ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                    <Activity size={16} />
                                </div>
                                <div>
                                    <span className="text-sm font-bold text-slate-700 dark:text-white">Self-Signed Issuer</span>
                                    {!clusterState.cert_manager_installed && (
                                        <p className="text-[10px] text-slate-400">Requires Cert Manager</p>
                                    )}
                                </div>
                            </div>
                            {clusterState.cluster_issuer_installed ? (
                                <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                                    ACTIVE
                                </span>
                            ) : (
                                <button
                                    id="install-self-signed-issuer-btn"
                                    onClick={() => handleInstallAction('install_self_signed_issuer')}
                                    disabled={!clusterState.cert_manager_installed || installingActions['install_self_signed_issuer']}
                                    className="mw-btn-primary py-1 px-3 text-[10px] flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                                >
                                    {installingActions['install_self_signed_issuer'] && <RefreshCw size={10} className="animate-spin" />}
                                    {installingActions['install_self_signed_issuer'] ? 'INSTALLING' : 'INSTALL'}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ServiceView;
