import React, { useState, useEffect } from 'react';
import {
    Briefcase, Database, Server, Activity, ArrowLeft, Monitor, Users, UserPlus, Edit, Trash2, Shield, RefreshCw, Download, Search, Key, CheckCircle2, AlertCircle, Eye, RefreshCcw, Network, Copy, Check
} from 'lucide-react';
import { useProjectLocalUsers } from '../../hooks/useResources';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import ResourceConfirmModal from '../../components/ResourceConfirmModal';
import { useNotification } from '../../providers/NotificationProvider';
import { ExternalNetworkAccessBlock } from '../../components/ServiceBlocks';
import apiClient from '../../services/api';

const ServiceView = ({
    context,
    selectedProjectId,
    selectedProject,
    onBack,
    projectsHook
}) => {
    const { getProjectState, refreshProjectState, getProjectCertManager, getProjectIssuerCert, getProjectCertDetails, renewProjectCertificate } = projectsHook;
    const darkMode = context?.darkMode ?? true;
    const [projectState, setProjectState] = useState(null);
    const [certData, setCertData] = useState(null);
    const [selectedCert, setSelectedCert] = useState(null);
    const [isCertModalOpen, setIsCertModalOpen] = useState(false);
    const [certDetails, setCertDetails] = useState(null);
    const [loadingCertDetails, setLoadingCertDetails] = useState(false);
    const [certDetailsError, setCertDetailsError] = useState(null);
    const [copiedPem, setCopiedPem] = useState(false);
    const [showPem, setShowPem] = useState(false);
    const [renewingCertName, setRenewingCertName] = useState(null);
    const [refreshingCertManager, setRefreshingCertManager] = useState(false);
    const { showSuccess, showError } = useNotification();

    const handleViewCertDetails = async (cert) => {
        setSelectedCert(cert);
        setCertDetails(null);
        setCertDetailsError(null);
        setShowPem(false);
        setIsCertModalOpen(true);
        setLoadingCertDetails(true);
        try {
            if (getProjectCertDetails) {
                const data = await getProjectCertDetails(selectedProjectId, cert.name, cert.namespace);
                setCertDetails(data);
            }
        } catch (e) {
            console.error("Failed to fetch certificate details:", e);
            setCertDetailsError(e.response?.data?.detail || "Failed to load certificate details.");
        } finally {
            setLoadingCertDetails(false);
        }
    };

    const handleCopyPem = (pem) => {
        if (!pem) return;
        navigator.clipboard.writeText(pem);
        setCopiedPem(true);
        setTimeout(() => setCopiedPem(false), 2000);
    };

    const handleRenewCert = async (cert) => {
        if (!renewProjectCertificate || !cert) return;
        setRenewingCertName(cert.name);
        try {
            await renewProjectCertificate(selectedProjectId, cert.name, cert.namespace);
            showSuccess(`Renewal initiated for certificate '${cert.name}'.`);
            if (isCertModalOpen && selectedCert?.name === cert.name && getProjectCertDetails) {
                setTimeout(async () => {
                    try {
                        const data = await getProjectCertDetails(selectedProjectId, cert.name, cert.namespace);
                        setCertDetails(data);
                    } catch (err) {
                        console.debug("Error refreshing cert details after renewal:", err);
                    }
                }, 2000);
            }
            if (getProjectCertManager) {
                setTimeout(async () => {
                    try {
                        const cmData = await getProjectCertManager(selectedProjectId);
                        setCertData(cmData);
                    } catch (err) {
                        console.debug("Error refreshing cert manager data:", err);
                    }
                }, 2500);
            }
        } catch (e) {
            console.error("Failed to renew certificate:", e);
            showError(e.response?.data?.detail || "Failed to trigger certificate renewal.");
        } finally {
            setRenewingCertName(null);
        }
    };

    const handleRefreshCertManager = async () => {
        if (!getProjectCertManager || !selectedProjectId) return;
        setRefreshingCertManager(true);
        try {
            const data = await getProjectCertManager(selectedProjectId);
            setCertData(data);
            showSuccess("Certificate status & validity refreshed");
        } catch (err) {
            console.error("Failed to refresh certificate status:", err);
            showError("Failed to refresh certificates");
        } finally {
            setRefreshingCertManager(false);
        }
    };

    const handleDownloadCert = async () => {
        try {
            const response = await apiClient.get(`/projects/${selectedProjectId}/_download-haproxy-cert`, {
                responseType: 'blob'
            });
            const blob = new Blob([response.data], { type: 'application/x-pem-file' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `envoy-${selectedProject.name}.pem`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
            showSuccess("Certificate downloaded successfully");
        } catch (e) {
            console.error(e);
            showError("Failed to download HAProxy certificate. Ensure Envoy Gateway is active.");
        }
    };


    const localUsersHook = useProjectLocalUsers();
    const { items: localUsers, loading: loadingUsers, fetchItems: fetchUsers, deleteItem: deleteUser } = localUsersHook;

    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [deleteItem, setDeleteItem] = useState(null);
    const [isInstallingDex, setIsInstallingDex] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const [enableDex, setEnableDex] = useState(false);

    useEffect(() => {
        const fetchFeatureFlags = async () => {
            try {
                const baseUrl = apiClient.defaults.baseURL;
                const rootUrl = baseUrl.replace(/\/api\/v1\/?$/, '');
                const response = await fetch(`${rootUrl}/feature-flags`);
                if (response.ok) {
                    const data = await response.json();
                    setEnableDex(data.enable_dex ?? false);
                }
            } catch (err) {
                console.error("Failed to fetch feature flags in ServiceView:", err);
            }
        };
        fetchFeatureFlags();
    }, []);

    const handleSyncIntegrations = async () => {
        setIsSyncing(true);
        try {
            await projectsHook.executeAction(selectedProjectId, 'sync_project_integrations');
            showSuccess("Project integrations sync triggered");
            const newState = await getProjectState(selectedProjectId);
            setProjectState(newState);
        } catch (e) {
            console.error(e);
            showError("Failed to trigger integrations sync");
        } finally {
            setIsSyncing(false);
        }
    };

    const handleDownloadIssuerCert = async (name, kind, namespace) => {
        if (!getProjectIssuerCert) return;
        try {
            const data = await getProjectIssuerCert(selectedProjectId, name, kind, namespace);
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
        if (selectedProjectId) {
            getProjectState(selectedProjectId).then(setProjectState);
            if (getProjectCertManager) {
                getProjectCertManager(selectedProjectId).then(setCertData).catch(console.error);
            }

            timer = setInterval(() => {
                getProjectState(selectedProjectId).then(setProjectState);
                if (getProjectCertManager) {
                    getProjectCertManager(selectedProjectId).then(setCertData).catch(console.error);
                }
            }, 10000);
        } else {
            Promise.resolve().then(() => {
                setProjectState(null);
                setCertData(null);
            });
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [selectedProjectId, getProjectState, getProjectCertManager]);

    const projectUsers = localUsers.filter(u => u.project_id === selectedProjectId);

    const handleInstallDex = async () => {
        setIsInstallingDex(true);
        try {
            await projectsHook.executeAction(selectedProjectId, 'install_dex');
            showSuccess("Dex installation triggered for this project");
            const newState = await getProjectState(selectedProjectId);
            setProjectState(newState);
        } catch (e) {
            console.error(e);
            showError("Failed to trigger Dex installation");
        } finally {
            setIsInstallingDex(false);
        }
    };

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
            name: "Hive Metastore",
            icon: Database,
            count: projectState?.hive_metastore || 0,
            color: "text-amber-500",
            bg: "bg-amber-500/10"
        },
        {
            name: "Superset",
            icon: Activity,
            count: projectState?.superset || 0,
            color: "text-rose-500",
            bg: "bg-rose-500/10"
        },
        {
            name: "Airflow",
            icon: Activity,
            count: projectState?.airflow || 0,
            color: "text-cyan-500",
            bg: "bg-cyan-500/10"
        },
        {
            name: "Kafka",
            icon: RefreshCcw,
            count: projectState?.kafka || 0,
            color: "text-amber-500",
            bg: "bg-amber-500/10"
        },
        {
            name: "NiFi",
            icon: Network,
            count: projectState?.nifi || 0,
            color: "text-orange-500",
            bg: "bg-orange-500/10"
        }
    ];

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="mw-page-header flex items-center justify-between">
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
                            <button
                                onClick={async () => {
                                    if (refreshProjectState) {
                                        try {
                                            await refreshProjectState(selectedProjectId);
                                        } catch (e) {
                                            console.error("Failed to refresh project state:", e);
                                        }
                                    }
                                    const newState = await getProjectState(selectedProjectId);
                                    setProjectState(newState);
                                    if (getProjectCertManager) {
                                        const cmData = await getProjectCertManager(selectedProjectId);
                                        setCertData(cmData);
                                    }
                                }}
                                className="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors bg-slate-100 dark:bg-slate-800 rounded-xl"
                                title="Refresh Status"
                                id="refresh-project-status"
                            >
                                <RefreshCw size={18} />
                            </button>
                        </div>
                        <div className="flex items-center gap-4 mt-2">
                            <span className="flex items-center gap-1.5 text-sm text-slate-400">
                                Project ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedProject.id}</span>
                            </span>
                        </div>
                    </div>
                </div>

                <button
                    onClick={handleSyncIntegrations}
                    disabled={isSyncing || !selectedProject.ingress_domain}
                    className="mw-btn-primary px-6 py-2.5 flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                    id="project-sync-integrations-btn"
                >
                    {isSyncing ? <RefreshCw size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                    {isSyncing ? 'SYNCING...' : 'SYNC INTEGRATIONS'}
                </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7 gap-6">
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

            {/* Envoy Gateway Integration */}
            <div className="mw-card p-8 space-y-6 animate-in slide-in-from-bottom duration-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="mw-icon-box text-indigo-500">
                            <Activity size={24} />
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Envoy Gateway</h3>
                            <p className="text-sm text-slate-500 font-medium uppercase tracking-tight">Ingress Gateway controller for project routing</p>
                        </div>
                    </div>
                    {projectState?.ingress_ports && projectState.ingress_ports.length > 0 ? (
                        <div className="flex items-center gap-3">
                            <span className="text-sm font-bold bg-green-500/10 text-green-500 px-3 py-1.5 rounded-xl border border-green-500/20 flex items-center gap-1.5">
                                <span className="w-2 h-2 rounded-full bg-green-500" />
                                ACTIVE
                            </span>
                            <button
                                onClick={handleDownloadCert}
                                className="mw-btn-secondary px-6 py-2.5 flex items-center gap-2"
                                id="download-haproxy-cert-btn"
                                title="Download HAProxy SSL PEM Certificate"
                            >
                                <Download size={16} />
                                DOWNLOAD PEM CERT
                            </button>
                        </div>
                    ) : (
                        <span className="text-sm font-bold bg-slate-500/10 text-slate-500 px-3 py-1.5 rounded-xl border border-slate-500/20 flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-slate-500" />
                            INACTIVE
                        </span>
                    )}
                </div>

                {projectState?.ingress_ports && projectState.ingress_ports.length > 0 && (
                    <div className="border-t border-slate-100 dark:border-slate-800/80 pt-6">
                        <ExternalNetworkAccessBlock
                            darkMode={darkMode}
                            ports={projectState.ingress_ports.map(port => ({
                                label: port.name,
                                node_port: port.node_port,
                                port: port.port,
                                load_balancer_ips: projectState.envoy_gateway_service_type === 'LoadBalancer' ? (port.load_balancer_ips || []) : undefined,
                                scheme: 'https'
                            }))}
                            clusterNodes={projectState.cluster_node_ips?.map((ip, idx) => ({
                                ipv4: ip,
                                hostname: `Node ${idx + 1}`
                            })) || []}
                            guideTitle={projectState.envoy_gateway_service_type === 'LoadBalancer' ? "DNS Ingress Domain Setup" : "HAProxy Ingress Gateway Configuration"}
                            guideText={projectState.envoy_gateway_service_type === 'LoadBalancer' 
                                ? `To route external traffic to your project, configure a CNAME or A record for your domain <strong>${selectedProject.ingress_domain}</strong> to point to the LoadBalancer IP/hostname.`
                                : "To route external HTTPS (port 443) traffic to the Envoy Gateway NodePorts, configure your external HAProxy load balancer using SSL Termination (HTTP mode) with your custom SSL certificate."}
                            cliLanguage={projectState.envoy_gateway_service_type === 'LoadBalancer' ? undefined : "haproxy"}
                            cliTitle={projectState.envoy_gateway_service_type === 'LoadBalancer' ? undefined : "HAProxy Configuration"}
                            cliInfo={projectState.envoy_gateway_service_type === 'LoadBalancer' ? undefined : {
                                command: `global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5s
    timeout client  50s
    timeout server  50s

frontend ingress_443
    bind :443 ssl crt /etc/pki/tls/certs/haproxy.pem
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https
    default_backend envoy_gateway_backend

backend envoy_gateway_backend
    mode http
    balance roundrobin
${projectState.cluster_node_ips?.map((ip, idx) => `    server node${idx + 1} ${ip}:${projectState.ingress_ports[0].node_port} ssl verify none no-check-ssl check sni req.hdr(host)`).join('\n') || `    server node1 ${projectState.cluster_node_ips?.[0] || 'NODE_IP'}:${projectState.ingress_ports[0].node_port} ssl verify none no-check-ssl check sni req.hdr(host)`}
`
                            }}
                        />
                    </div>
                )}
            </div>

            {/* Dex OIDC Integration */}
            {enableDex && (
                <div className="mw-card p-8 space-y-6 animate-in slide-in-from-bottom duration-700">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="mw-icon-box text-indigo-500">
                                <Shield size={24} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Dex OIDC Integration</h3>
                                <p className="text-sm text-slate-500 font-medium uppercase tracking-tight">Federated identity provider for project components</p>
                            </div>
                        </div>
                        {projectState?.dex_installed ? (
                            <div className="flex items-center gap-3">
                                <span className="text-sm font-bold bg-green-500/10 text-green-500 px-3 py-1.5 rounded-xl border border-green-500/20 flex items-center gap-1.5">
                                    <span className="w-2 h-2 rounded-full bg-green-500" />
                                    {projectState.dex_version || "ACTIVE"}
                                </span>
                                <button
                                    onClick={handleInstallDex}
                                    disabled={isInstallingDex}
                                    className="mw-btn-secondary px-6 py-2.5 flex items-center gap-2"
                                >
                                    {isInstallingDex ? <RefreshCw size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                                    UPDATE DEX
                                </button>
                            </div>
                        ) : (
                            <button
                                onClick={handleInstallDex}
                                disabled={isInstallingDex}
                                className="mw-btn-primary px-6 py-2.5 flex items-center gap-2"
                            >
                                {isInstallingDex ? <RefreshCw size={16} className="animate-spin" /> : <Shield size={16} />}
                                {isInstallingDex ? 'INSTALLING...' : 'INSTALL DEX OIDC'}
                            </button>
                        )}
                    </div>

                    {projectState?.dex_installed && (
                        <div className="mt-6 border-t border-slate-100 dark:border-slate-800/80 pt-6 space-y-4" id="dex-connection-details">
                            <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400">Connection Details</h4>
                            <div className="grid grid-cols-1 gap-4">
                                <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800/50">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">OIDC Discovery URL</span>
                                    <div className="mt-1 flex items-center justify-between gap-2">
                                        <a
                                            href={selectedProject.ingress_domain 
                                                ? `https://dex.${selectedProject.ingress_domain}/dex/.well-known/openid-configuration` 
                                                : `http://dex.${selectedProject.k8s_namespace || selectedProject.name}.svc.cluster.local:5556/dex/.well-known/openid-configuration`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-sm font-mono text-indigo-500 hover:text-indigo-600 dark:text-indigo-400 dark:hover:text-indigo-300 break-all transition-colors"
                                        >
                                            {selectedProject.ingress_domain 
                                                ? `https://dex.${selectedProject.ingress_domain}/dex/.well-known/openid-configuration` 
                                                : `http://dex.${selectedProject.k8s_namespace || selectedProject.name}.svc.cluster.local:5556/dex/.well-known/openid-configuration`}
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Project Local Users Management */}
            {enableDex && (
                <div className="mw-card p-8 space-y-8 animate-in slide-in-from-bottom duration-700">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="mw-icon-box text-indigo-500">
                                <Users size={24} />
                            </div>
                            <div>
                                <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Local User Management</h3>
                                <p className="text-sm text-slate-500 font-medium uppercase tracking-tight">Manage project-scoped credentials for OIDC integration</p>
                            </div>
                        </div>
                        <button
                            onClick={() => setIsCreateOpen(true)}
                            className="mw-btn-primary px-6 py-2.5 flex items-center gap-2"
                        >
                            <UserPlus size={16} />
                            ADD LOCAL USER
                        </button>
                    </div>

                    {loadingUsers ? (
                        <div className="text-center py-8 text-slate-500">
                            Loading users...
                        </div>
                    ) : projectUsers.length === 0 ? (
                        <div className="text-center py-8 text-slate-500">
                            No local users configured for this project.
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-slate-200 dark:border-slate-800 text-xs font-bold uppercase tracking-widest text-slate-400">
                                        <th className="py-4 px-6">Username</th>
                                        <th className="py-4 px-6">Email Address</th>
                                        <th className="py-4 px-6 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {projectUsers.map(user => (
                                        <tr key={user.id} className="border-b border-slate-100 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-900/20 transition-colors">
                                            <td className="py-4 px-6 font-semibold text-slate-900 dark:text-white">{user.username}</td>
                                            <td className="py-4 px-6 text-slate-500 dark:text-slate-400">{user.email}</td>
                                            <td className="py-4 px-6 text-right flex justify-end gap-2">
                                                <button
                                                    onClick={() => setEditItem(user)}
                                                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400 hover:text-blue-500 transition-colors"
                                                    title="Edit User"
                                                >
                                                    <Edit size={16} />
                                                </button>
                                                <button
                                                    onClick={() => setDeleteItem(user)}
                                                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400 hover:text-rose-500 transition-colors"
                                                    title="Delete User"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* Create Modal */}
            <Modal
                isOpen={isCreateOpen}
                onClose={() => setIsCreateOpen(false)}
                title="Add Local User"
                darkMode={darkMode}
            >
                <DynamicForm
                    entityPath="/project-local-users"
                    mode="create"
                    initialData={{ project_id: selectedProjectId }}
                    darkMode={darkMode}
                    onSuccess={async () => {
                        setIsCreateOpen(false);
                        await fetchUsers();
                    }}
                    onCancel={() => setIsCreateOpen(false)}
                />
            </Modal>

            {/* Edit Modal */}
            <Modal
                isOpen={!!editItem}
                onClose={() => setEditItem(null)}
                title="Edit Local User"
                darkMode={darkMode}
            >
                {editItem && (
                    <DynamicForm
                        entityPath="/project-local-users"
                        mode="edit"
                        initialData={editItem}
                        darkMode={darkMode}
                        onSuccess={async () => {
                            setEditItem(null);
                            await fetchUsers();
                        }}
                        onCancel={() => setEditItem(null)}
                    />
                )}
            </Modal>

            {/* Delete Confirmation Modal */}
            {deleteItem && (
                <ResourceConfirmModal
                    isOpen={!!deleteItem}
                    onClose={() => setDeleteItem(null)}
                    onConfirm={async (confirmName) => {
                        await deleteUser(deleteItem.id, confirmName);
                        await fetchUsers();
                    }}
                    resourceName={deleteItem.username}
                    title="Delete Local User"
                    message="Are you sure you want to delete this local user?"
                    darkMode={darkMode}
                />
            )}
            {certData && (
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
                        <button
                            onClick={handleRefreshCertManager}
                            disabled={refreshingCertManager}
                            className="mw-btn-secondary py-1.5 px-3 text-xs flex items-center gap-2"
                            title="Refresh Certificates & Check Validity"
                            id="refresh-cert-manager-btn"
                        >
                            <RefreshCw size={14} className={refreshingCertManager ? "animate-spin text-indigo-500" : ""} />
                            REFRESH
                        </button>
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
                                        No Cert Manager resources found in this project.
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
                                                                    <span
                                                                        title={cert.status_reason || cert.status}
                                                                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                                                            cert.status === 'Ready'
                                                                                ? 'bg-green-500/10 text-green-500'
                                                                                : cert.status === 'Expired'
                                                                                ? 'bg-amber-500/10 text-amber-500'
                                                                                : 'bg-red-500/10 text-red-500'
                                                                        }`}
                                                                    >
                                                                        {cert.status}
                                                                    </span>
                                                                    <div className="flex items-center gap-2">
                                                                        <button
                                                                            onClick={() => handleViewCertDetails(cert)}
                                                                            className="mw-btn-secondary py-1 px-2.5 text-xs flex items-center gap-1.5"
                                                                            title="View Details"
                                                                            id={`view-cert-details-${cert.name}`}
                                                                        >
                                                                            <Eye size={12} />
                                                                            DETAILS
                                                                        </button>
                                                                        <button
                                                                            onClick={() => handleRenewCert(cert)}
                                                                            disabled={renewingCertName === cert.name}
                                                                            className="mw-btn-secondary py-1 px-2.5 text-xs flex items-center gap-1.5 disabled:opacity-50 text-indigo-500 hover:text-indigo-600 dark:text-indigo-400"
                                                                            title="Renew Certificate"
                                                                            id={`renew-cert-${cert.name}`}
                                                                        >
                                                                            <RefreshCw size={12} className={renewingCertName === cert.name ? "animate-spin" : ""} />
                                                                            {renewingCertName === cert.name ? "RENEWING..." : "RENEW"}
                                                                        </button>
                                                                    </div>
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
                                                                <span
                                                                    title={cert.status_reason || cert.status}
                                                                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                                                        cert.status === 'Ready'
                                                                            ? 'bg-green-500/10 text-green-500'
                                                                            : cert.status === 'Expired'
                                                                            ? 'bg-amber-500/10 text-amber-500'
                                                                            : 'bg-red-500/10 text-red-500'
                                                                    }`}
                                                                >
                                                                    {cert.status}
                                                                </span>
                                                                <div className="flex items-center gap-2">
                                                                    <button
                                                                        onClick={() => handleViewCertDetails(cert)}
                                                                        className="mw-btn-secondary py-1 px-2.5 text-xs flex items-center gap-1.5"
                                                                        title="View Details"
                                                                        id={`view-orphan-cert-details-${cert.name}`}
                                                                    >
                                                                        <Eye size={12} />
                                                                        DETAILS
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleRenewCert(cert)}
                                                                        disabled={renewingCertName === cert.name}
                                                                        className="mw-btn-secondary py-1 px-2.5 text-xs flex items-center gap-1.5 disabled:opacity-50 text-indigo-500 hover:text-indigo-600 dark:text-indigo-400"
                                                                        title="Renew Certificate"
                                                                        id={`renew-orphan-cert-${cert.name}`}
                                                                    >
                                                                        <RefreshCw size={12} className={renewingCertName === cert.name ? "animate-spin" : ""} />
                                                                        {renewingCertName === cert.name ? "RENEWING..." : "RENEW"}
                                                                    </button>
                                                                </div>
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
                    isOpen={isCertModalOpen}
                    onClose={() => {
                        setIsCertModalOpen(false);
                        setSelectedCert(null);
                        setCertDetails(null);
                        setCertDetailsError(null);
                    }}
                    title={`Certificate: ${selectedCert.name}`}
                    maxWidth="max-w-3xl"
                    darkMode={darkMode}
                >
                    {loadingCertDetails ? (
                        <div className="flex flex-col items-center justify-center py-12 space-y-3">
                            <RefreshCw size={32} className="animate-spin text-indigo-500" />
                            <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                                Inspecting certificate & validating against Project CA...
                            </p>
                        </div>
                    ) : certDetailsError ? (
                        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 flex items-start gap-3 text-sm">
                            <AlertCircle size={20} className="shrink-0 mt-0.5" />
                            <div>
                                <h4 className="font-bold">Error Loading Certificate Details</h4>
                                <p className="mt-1 text-xs">{certDetailsError}</p>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Validation Status Banner */}
                            {certDetails?.validation && (
                                <div
                                    className={`p-4 rounded-2xl border flex items-start justify-between gap-4 ${
                                        certDetails.validation.is_valid
                                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300'
                                            : 'bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-300'
                                    }`}
                                >
                                    <div className="flex items-start gap-3">
                                        {certDetails.validation.is_valid ? (
                                            <CheckCircle2 size={24} className="text-emerald-500 shrink-0 mt-0.5" />
                                        ) : (
                                            <AlertCircle size={24} className="text-rose-500 shrink-0 mt-0.5" />
                                        )}
                                        <div>
                                            <h4 className="font-bold text-sm">
                                                {certDetails.validation.is_valid
                                                    ? 'Certificate Validated Against Project CA'
                                                    : 'Certificate Validation Failed'}
                                            </h4>
                                            <p className="text-xs mt-1 text-slate-600 dark:text-slate-300 leading-relaxed font-mono">
                                                {certDetails.validation.message}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 shrink-0">
                                        <span
                                            className={`px-2.5 py-1 text-xs font-bold rounded-lg uppercase tracking-wider ${
                                                certDetails.validation.is_valid
                                                    ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                                                    : 'bg-rose-500/20 text-rose-600 dark:text-rose-400'
                                            }`}
                                        >
                                            {certDetails.validation.status || (certDetails.validation.is_valid ? 'VALID' : 'INVALID')}
                                        </span>
                                        <button
                                            onClick={() => handleRenewCert(selectedCert)}
                                            disabled={renewingCertName === selectedCert.name}
                                            className="mw-btn-primary py-1 px-3 text-xs flex items-center gap-1.5"
                                            id="modal-renew-cert-btn"
                                            title="Renew Certificate with Project CA"
                                        >
                                            <RefreshCw size={12} className={renewingCertName === selectedCert.name ? "animate-spin" : ""} />
                                            {renewingCertName === selectedCert.name ? "RENEWING..." : "RENEW"}
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Project CA Details */}
                            {certDetails?.ca && (
                                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-3">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <Shield size={18} className="text-indigo-500" />
                                            <h4 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-200">
                                                Project CA Details
                                            </h4>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span
                                                className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                                                    certDetails.ca.is_valid
                                                        ? 'bg-emerald-500/10 text-emerald-500'
                                                        : 'bg-rose-500/10 text-rose-500'
                                                }`}
                                            >
                                                {certDetails.ca.is_valid ? 'CA VALID' : 'CA INVALID'}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                                        <div>
                                            <span className="text-slate-400 uppercase font-bold text-[10px] block">CA Common Name</span>
                                            <span className="font-semibold text-slate-700 dark:text-slate-200 font-mono">
                                                {certDetails.ca.subject?.common_name || certDetails.ca.name || 'N/A'}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-slate-400 uppercase font-bold text-[10px] block">CA Secret</span>
                                            <span className="font-semibold text-slate-700 dark:text-slate-200 font-mono">
                                                {certDetails.ca.name || 'N/A'}
                                            </span>
                                        </div>
                                        {certDetails.ca.not_before && (
                                            <div>
                                                <span className="text-slate-400 uppercase font-bold text-[10px] block">CA Validity Window</span>
                                                <span className="font-semibold text-slate-700 dark:text-slate-200 font-mono">
                                                    {new Date(certDetails.ca.not_before).toLocaleDateString()} — {new Date(certDetails.ca.not_after).toLocaleDateString()}
                                                </span>
                                            </div>
                                        )}
                                        {certDetails.ca.serial_number && (
                                            <div>
                                                <span className="text-slate-400 uppercase font-bold text-[10px] block">CA Serial Number</span>
                                                <span className="font-semibold text-slate-700 dark:text-slate-200 font-mono truncate block" title={certDetails.ca.serial_number}>
                                                    {certDetails.ca.serial_number}
                                                </span>
                                            </div>
                                        )}
                                        {certDetails.ca.subject_key_identifier && (
                                            <div className="sm:col-span-2">
                                                <span className="text-slate-400 uppercase font-bold text-[10px] block">Subject Key Identifier (SKI)</span>
                                                <span className="font-mono text-[11px] text-slate-600 dark:text-slate-300 break-all block">
                                                    {certDetails.ca.subject_key_identifier}
                                                </span>
                                            </div>
                                        )}
                                    </div>

                                    {certDetails.validation?.aki_matches_ski !== null && certDetails.validation?.aki_matches_ski !== undefined && (
                                        <div className="pt-2 border-t border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between text-xs">
                                            <span className="text-slate-500 dark:text-slate-400">Authority Key ID Match:</span>
                                            {certDetails.validation.aki_matches_ski ? (
                                                <span className="text-emerald-500 font-bold flex items-center gap-1">
                                                    <CheckCircle2 size={13} /> Matches Project CA SKI
                                                </span>
                                            ) : (
                                                <span className="text-amber-500 font-bold flex items-center gap-1">
                                                    <AlertCircle size={13} /> Mismatch with Project CA SKI (CA was rotated or reissued)
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Certificate Details */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Namespace</span>
                                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">{certDetails?.namespace || selectedCert.namespace}</p>
                                </div>
                                <div className="space-y-1">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Secret Name</span>
                                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">{certDetails?.secret_name || selectedCert.secret_name || 'N/A'}</p>
                                </div>
                                <div className="space-y-1">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Issuer Reference</span>
                                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                                        {certDetails?.issuer_ref?.kind || selectedCert.issuer_kind}: {certDetails?.issuer_ref?.name || selectedCert.issuer_name}
                                    </p>
                                </div>
                                <div className="space-y-1">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Cert-Manager Status</span>
                                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{selectedCert.status}</p>
                                </div>

                                {certDetails?.certificate?.subject?.common_name && (
                                    <div className="space-y-1">
                                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Subject (CN)</span>
                                        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">{certDetails.certificate.subject.common_name}</p>
                                    </div>
                                )}
                                {certDetails?.certificate?.signature_algorithm && (
                                    <div className="space-y-1">
                                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Signature Algorithm</span>
                                        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">{certDetails.certificate.signature_algorithm}</p>
                                    </div>
                                )}

                                {(certDetails?.certificate?.not_before || selectedCert.not_before) && (
                                    <div className="space-y-1">
                                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Not Before</span>
                                        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">
                                            {new Date(certDetails?.certificate?.not_before || selectedCert.not_before).toLocaleString()}
                                        </p>
                                    </div>
                                )}
                                {(certDetails?.certificate?.not_after || selectedCert.not_after) && (
                                    <div className="space-y-1">
                                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Not After (Expiration)</span>
                                        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 font-mono">
                                            {new Date(certDetails?.certificate?.not_after || selectedCert.not_after).toLocaleString()}
                                        </p>
                                    </div>
                                )}

                                {certDetails?.certificate?.serial_number && (
                                    <div className="space-y-1 col-span-2">
                                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Serial Number</span>
                                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 font-mono break-all">{certDetails.certificate.serial_number}</p>
                                    </div>
                                )}
                                {certDetails?.certificate?.authority_key_identifier && (
                                    <div className="space-y-1 col-span-2">
                                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Authority Key Identifier (AKI)</span>
                                        <p className="text-xs font-mono text-slate-600 dark:text-slate-300 break-all">{certDetails.certificate.authority_key_identifier}</p>
                                    </div>
                                )}
                            </div>

                            {/* DNS Names */}
                            {((certDetails?.certificate?.dns_names && certDetails.certificate.dns_names.length > 0) || (selectedCert.dns_names && selectedCert.dns_names.length > 0)) && (
                                <div className="space-y-2">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">DNS Names (Domains)</span>
                                    <div className="flex flex-wrap gap-2">
                                        {(certDetails?.certificate?.dns_names || selectedCert.dns_names).map(domain => (
                                            <span key={domain} className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 rounded-lg text-xs font-mono text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                                                {domain}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Conditions */}
                            {((certDetails?.conditions && certDetails.conditions.length > 0) || (selectedCert.conditions && selectedCert.conditions.length > 0)) && (
                                <div className="space-y-3">
                                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Cert-Manager Conditions</span>
                                    <div className="space-y-2 max-h-40 overflow-y-auto">
                                        {(certDetails?.conditions || selectedCert.conditions).map((cond, idx) => (
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

                            {/* PEM Certificate Display */}
                            {certDetails?.certificate?.pem && (
                                <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                                    <div className="flex items-center justify-between">
                                        <button
                                            onClick={() => setShowPem(!showPem)}
                                            className="text-xs font-bold uppercase tracking-wider text-indigo-500 hover:text-indigo-600 transition-colors"
                                        >
                                            {showPem ? 'Hide Raw Certificate (PEM)' : 'View Raw Certificate (PEM)'}
                                        </button>
                                        <button
                                            onClick={() => handleCopyPem(certDetails.certificate.pem)}
                                            className="mw-btn-secondary py-1 px-2.5 text-xs flex items-center gap-1.5"
                                            title="Copy PEM Certificate"
                                        >
                                            {copiedPem ? <Check size={12} className="text-green-500" /> : <Copy size={12} />}
                                            {copiedPem ? 'COPIED' : 'COPY PEM'}
                                        </button>
                                    </div>
                                    {showPem && (
                                        <textarea
                                            readOnly
                                            rows={6}
                                            value={certDetails.certificate.pem}
                                            className="w-full text-[11px] font-mono p-3 rounded-xl bg-slate-900 text-slate-200 border border-slate-800 focus:outline-none resize-none"
                                        />
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </Modal>
            )}
        </div>
    );
};

export default ServiceView;

