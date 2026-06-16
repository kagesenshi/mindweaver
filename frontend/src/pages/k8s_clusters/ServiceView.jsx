import React, { useState, useEffect } from 'react';
import {
    Activity, Monitor, RefreshCw, Shield, Key, CheckCircle2, AlertCircle, Eye, Download
} from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import Modal from '../../components/Modal';

const ServiceView = ({
    selectedClusterId,
    selectedCluster,
    onBack,
    clustersHook
}) => {
    const { getClusterState, getClusterCertManager, getClusterIssuerCert, refreshClusterState } = clustersHook;
    const [clusterState, setClusterState] = useState(null);
    const [certData, setCertData] = useState(null);
    const [selectedCert, setSelectedCert] = useState(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [installingActions, setInstallingActions] = useState({});
    const { showSuccess, showError } = useNotification();

    const handleDownloadIssuerCert = async (name, kind, namespace) => {
        if (!getClusterIssuerCert) return;
        try {
            const data = await getClusterIssuerCert(selectedClusterId, name, kind, namespace);
            if (data && data.pem) {
                const blob = new Blob([data.pem], { type: 'application/x-x509-ca-cert' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename || `${name}-ca.crt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                showSuccess("CA Certificate downloaded");
            } else {
                showError("No certificate data returned");
            }
        } catch (e) {
            console.error(e);
            const errMsg = e.response?.data?.detail || "Failed to download CA certificate";
            showError(errMsg);
        }
    };

    useEffect(() => {
        let timer;
        if (selectedClusterId && getClusterState) {
            getClusterState(selectedClusterId).then(newState => {
                setClusterState(newState);
                if (newState.cert_manager_installed && getClusterCertManager) {
                    getClusterCertManager(selectedClusterId).then(setCertData).catch(console.error);
                }
            });

            timer = setInterval(() => {
                getClusterState(selectedClusterId).then(newState => {
                    setClusterState(newState);
                    if (newState.cert_manager_installed && getClusterCertManager) {
                        getClusterCertManager(selectedClusterId).then(setCertData).catch(console.error);
                    }
                });
            }, 10000);
        } else {
            Promise.resolve().then(() => {
                setClusterState(null);
                setCertData(null);
            });
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [selectedClusterId, getClusterState, getClusterCertManager]);

    const handleRefresh = async () => {
        if (!refreshClusterState) return;
        setIsRefreshing(true);
        try {
            const newState = await refreshClusterState(selectedClusterId);
            setClusterState(newState);
            if (newState.cert_manager_installed && getClusterCertManager) {
                const cmData = await getClusterCertManager(selectedClusterId);
                setCertData(cmData);
            }
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
                        <div className="flex items-center justify-between mb-4">
                            <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Core Integrations</p>
                            <button 
                                id="sync-core-integrations-btn"
                                onClick={() => handleInstallAction('sync_core_integrations')}
                                disabled={installingActions['sync_core_integrations']}
                                className="mw-btn-primary py-1.5 px-3 text-xs flex items-center gap-2"
                            >
                                {installingActions['sync_core_integrations'] && <RefreshCw size={12} className="animate-spin" />}
                                {installingActions['sync_core_integrations'] ? 'SYNCING...' : 'SYNC INTEGRATIONS'}
                            </button>
                        </div>
                        
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
                                <span className="text-[10px] font-bold bg-slate-100 text-slate-400 px-2 py-0.5 rounded">
                                    INACTIVE
                                </span>
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
                                <span className="text-[10px] font-bold bg-slate-100 text-slate-400 px-2 py-0.5 rounded">
                                    INACTIVE
                                </span>
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
                                <span className="text-[10px] font-bold bg-slate-100 text-slate-400 px-2 py-0.5 rounded">
                                    INACTIVE
                                </span>
                            )}
                        </div>

                        {/* Envoy Gateway */}
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${clusterState.envoy_gateway_installed ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                    <Activity size={16} />
                                </div>
                                <span className="text-sm font-bold text-slate-700 dark:text-white">Envoy Gateway</span>
                            </div>
                            {clusterState.envoy_gateway_installed ? (
                                <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                                    {clusterState.envoy_gateway_version || "ACTIVE"}
                                </span>
                            ) : (
                                <span className="text-[10px] font-bold bg-slate-100 text-slate-400 px-2 py-0.5 rounded">
                                    INACTIVE
                                </span>
                            )}
                        </div>

                        {/* Solr Operator */}
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${clusterState.solr_operator_installed ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                    <Activity size={16} />
                                </div>
                                <span className="text-sm font-bold text-slate-700 dark:text-white">Solr Operator</span>
                            </div>
                            {clusterState.solr_operator_installed ? (
                                <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                                    {clusterState.solr_operator_version || "ACTIVE"}
                                </span>
                            ) : (
                                <span className="text-[10px] font-bold bg-slate-100 text-slate-400 px-2 py-0.5 rounded">
                                    INACTIVE
                                </span>
                            )}
                        </div>

                        {/* Kafka Operator */}
                        <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${clusterState.kafka_operator_installed ? 'bg-indigo-500 text-white' : 'bg-slate-200 text-slate-400'}`}>
                                    <Activity size={16} />
                                </div>
                                <span className="text-sm font-bold text-slate-700 dark:text-white">Kafka Operator</span>
                            </div>
                            {clusterState.kafka_operator_installed ? (
                                <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                                    {clusterState.kafka_operator_version || "ACTIVE"}
                                </span>
                            ) : (
                                <span className="text-[10px] font-bold bg-slate-100 text-slate-400 px-2 py-0.5 rounded">
                                    INACTIVE
                                </span>
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
                                        <p className="text-[10px] text-slate-400 font-medium">Requires Cert Manager</p>
                                    )}
                                </div>
                            </div>
                            {clusterState.cluster_issuer_installed ? (
                                <span className="text-[10px] font-bold bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                                    ACTIVE
                                </span>
                            ) : (
                                <span className="text-[10px] font-bold bg-slate-100 text-slate-400 px-2 py-0.5 rounded">
                                    INACTIVE
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {clusterState.cert_manager_installed && certData && (
                <div className="mw-card p-8 space-y-8 animate-in slide-in-from-bottom duration-700">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="mw-icon-box text-indigo-500">
                                <Shield size={24} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Cert Manager Resources</h3>
                                <p className="text-sm text-slate-500 font-medium uppercase tracking-tight">Active Issuers & Issued Certificates</p>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6">
                        {(() => {
                            const grouped = {};
                            const issuers = certData.issuers || [];
                            const certificates = certData.certificates || [];

                            issuers.forEach(issuer => {
                                grouped[`${issuer.kind}/${issuer.name}`] = {
                                    issuer,
                                    certs: []
                                };
                            });

                            const orphanCerts = [];
                            certificates.forEach(cert => {
                                const key = `${cert.issuer_kind}/${cert.issuer_name}`;
                                if (grouped[key]) {
                                    grouped[key].certs.push(cert);
                                } else {
                                    orphanCerts.push(cert);
                                }
                            });

                            const hasResources = issuers.length > 0 || certificates.length > 0;

                            if (!hasResources) {
                                return (
                                    <div className="text-center py-8 text-slate-500">
                                        No Cert Manager resources found in this cluster.
                                    </div>
                                );
                            }

                            return (
                                <div className="grid grid-cols-1 gap-6">
                                    {Object.entries(grouped).map(([key, group]) => (
                                        <div key={key} className="bg-slate-50/50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/50 space-y-4">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 bg-indigo-500/10 text-indigo-500 rounded">
                                                        {group.issuer.kind}
                                                    </span>
                                                    <h4 className="text-lg font-bold text-slate-900 dark:text-white">{group.issuer.name}</h4>
                                                    {group.issuer.namespace && (
                                                        <span className="text-xs text-slate-400 font-mono">
                                                            namespace: {group.issuer.namespace}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <button
                                                        onClick={() => handleDownloadIssuerCert(group.issuer.name, group.issuer.kind, group.issuer.namespace)}
                                                        className="mw-btn-secondary py-1 px-2.5 text-xs flex items-center gap-1.5"
                                                        title="Download CA Certificate"
                                                    >
                                                        <Download size={12} />
                                                        CA CERT
                                                    </button>
                                                    <div className="flex items-center gap-1.5">
                                                        {group.issuer.status === 'Ready' ? (
                                                            <CheckCircle2 size={16} className="text-green-500" />
                                                        ) : (
                                                            <AlertCircle size={16} className="text-red-500" />
                                                        )}
                                                        <span className={`text-xs font-bold uppercase tracking-wider ${group.issuer.status === 'Ready' ? 'text-green-500' : 'text-red-500'}`}>
                                                            {group.issuer.status}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="ml-2 pl-4 border-l border-slate-200 dark:border-slate-800 space-y-3">
                                                <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Issued Certificates ({group.certs.length})</p>
                                                {group.certs.length === 0 ? (
                                                    <p className="text-sm text-slate-500 italic">No certificates issued by this issuer.</p>
                                                ) : (
                                                    <div className="grid grid-cols-1 gap-2">
                                                        {group.certs.map(cert => (
                                                            <div key={cert.name} className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                                                                <div className="flex items-center gap-3">
                                                                    <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-500">
                                                                        <Key size={16} />
                                                                    </div>
                                                                    <div>
                                                                        <span className="text-sm font-bold text-slate-700 dark:text-white">{cert.name}</span>
                                                                        <div className="flex items-center gap-2 mt-0.5">
                                                                            <span className="text-[10px] text-slate-400 font-mono">ns: {cert.namespace}</span>
                                                                            {cert.secret_name && (
                                                                                <span className="text-[10px] text-slate-400 font-mono">• secret: {cert.secret_name}</span>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-4">
                                                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${cert.status === 'Ready' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                                                                        {cert.status}
                                                                    </span>
                                                                    <button
                                                                        onClick={() => {
                                                                            setSelectedCert(cert);
                                                                            setIsModalOpen(true);
                                                                        }}
                                                                        className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-500 transition-colors"
                                                                        title="View Details"
                                                                    >
                                                                        <Eye size={16} />
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}

                                    {orphanCerts.length > 0 && (
                                        <div className="bg-slate-50/50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-200/50 dark:border-slate-800/50 space-y-4">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 bg-yellow-500/10 text-yellow-500 rounded">
                                                        External / Orphan
                                                    </span>
                                                    <h4 className="text-lg font-bold text-slate-900 dark:text-white">Other Certificates</h4>
                                                </div>
                                            </div>

                                            <div className="ml-2 pl-4 border-l border-slate-200 dark:border-slate-800 space-y-3">
                                                <div className="grid grid-cols-1 gap-2">
                                                    {orphanCerts.map(cert => (
                                                        <div key={cert.name} className="flex items-center justify-between p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                                                            <div className="flex items-center gap-3">
                                                                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-500">
                                                                    <Key size={16} />
                                                                </div>
                                                                <div>
                                                                    <span className="text-sm font-bold text-slate-700 dark:text-white">{cert.name}</span>
                                                                    <div className="flex items-center gap-2 mt-0.5">
                                                                        <span className="text-[10px] text-slate-400 font-mono">ns: {cert.namespace}</span>
                                                                        <span className="text-[10px] text-slate-400">• issuer: {cert.issuer_kind}/{cert.issuer_name}</span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-4">
                                                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${cert.status === 'Ready' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                                                                    {cert.status}
                                                                </span>
                                                                <button
                                                                    onClick={() => {
                                                                        setSelectedCert(cert);
                                                                        setIsModalOpen(true);
                                                                    }}
                                                                    className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg text-slate-500 transition-colors"
                                                                    title="View Details"
                                                                >
                                                                    <Eye size={16} />
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })()}
                    </div>
                </div>
            )}

            {selectedCert && (
                <Modal
                    isOpen={isModalOpen}
                    onClose={() => {
                        setIsModalOpen(false);
                        setSelectedCert(null);
                    }}
                    title={`Certificate: ${selectedCert.name}`}
                    maxWidth="max-w-2xl"
                >
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Namespace</span>
                                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{selectedCert.namespace}</p>
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Secret Name</span>
                                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">{selectedCert.secret_name || 'N/A'}</p>
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Issuer Reference</span>
                                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                                    {selectedCert.issuer_kind}: {selectedCert.issuer_name}
                                </p>
                            </div>
                            <div className="space-y-1">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Status</span>
                                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{selectedCert.status}</p>
                            </div>
                            {selectedCert.not_before && (
                                <div className="space-y-1">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Not Before</span>
                                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">{new Date(selectedCert.not_before).toLocaleString()}</p>
                                </div>
                            )}
                            {selectedCert.not_after && (
                                <div className="space-y-1">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Not After (Expiration)</span>
                                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">{new Date(selectedCert.not_after).toLocaleString()}</p>
                                </div>
                            )}
                        </div>

                        {selectedCert.dns_names && selectedCert.dns_names.length > 0 && (
                            <div className="space-y-2">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">DNS Names (Domains)</span>
                                <div className="flex flex-wrap gap-2">
                                    {selectedCert.dns_names.map(domain => (
                                        <span key={domain} className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 rounded-lg text-xs font-mono text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                                            {domain}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {selectedCert.conditions && selectedCert.conditions.length > 0 && (
                            <div className="space-y-3">
                                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Conditions</span>
                                <div className="space-y-2 max-h-48 overflow-y-auto">
                                    {selectedCert.conditions.map((cond, idx) => (
                                        <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 flex items-start justify-between gap-4 text-xs">
                                            <div className="space-y-1">
                                                <div className="font-bold text-slate-700 dark:text-slate-200">{cond.type}</div>
                                                {cond.message && <div className="text-slate-500 font-mono">{cond.message}</div>}
                                            </div>
                                            <span className={`font-bold uppercase tracking-wider px-2 py-0.5 rounded ${cond.status === 'True' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                                                {cond.status}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </Modal>
            )}
        </div>
    );
};

export default ServiceView;
