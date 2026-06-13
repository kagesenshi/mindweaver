import React, { useState, useEffect } from 'react';
import {
    Briefcase, Database, Server, Activity, ArrowLeft, Monitor, Users, UserPlus, Edit, Trash2, Shield, RefreshCw, Download, Search
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
    const { darkMode } = context || {};
    const { getProjectState, refreshProjectState } = projectsHook;
    const [projectState, setProjectState] = useState(null);
    const { showSuccess, showError } = useNotification();

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
    const [isDeployingGateway, setIsDeployingGateway] = useState(false);
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

    const handleDeployGateway = async () => {
        setIsDeployingGateway(true);
        try {
            await projectsHook.executeAction(selectedProjectId, 'deploy_gateway');
            showSuccess("Envoy Gateway deployment triggered for this project");
            const newState = await getProjectState(selectedProjectId);
            setProjectState(newState);
        } catch (e) {
            console.error(e);
            showError("Failed to trigger Envoy Gateway deployment");
        } finally {
            setIsDeployingGateway(false);
        }
    };

    useEffect(() => {
        let timer;
        if (selectedProjectId) {
            getProjectState(selectedProjectId).then(setProjectState);

            timer = setInterval(() => {
                getProjectState(selectedProjectId).then(setProjectState);
            }, 10000);
        } else {
            Promise.resolve().then(() => setProjectState(null));
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [selectedProjectId, getProjectState]);

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
            name: "Ranger",
            icon: Shield,
            count: projectState?.ranger || 0,
            color: "text-emerald-500",
            bg: "bg-emerald-500/10"
        },
        {
            name: "Solr",
            icon: Search,
            count: projectState?.solr || 0,
            color: "text-cyan-500",
            bg: "bg-cyan-500/10"
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
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
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
                            <button
                                onClick={handleDeployGateway}
                                disabled={isDeployingGateway}
                                className="mw-btn-secondary px-6 py-2.5 flex items-center gap-2"
                                id="redeploy-gateway-btn"
                            >
                                {isDeployingGateway ? <RefreshCw size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                                UPDATE GATEWAY
                            </button>
                        </div>
                    ) : (
                        <button
                            onClick={handleDeployGateway}
                            disabled={isDeployingGateway || !selectedProject.ingress_domain}
                            className="mw-btn-primary px-6 py-2.5 flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                            id="deploy-gateway-btn"
                        >
                            {isDeployingGateway ? <RefreshCw size={16} className="animate-spin" /> : <Activity size={16} />}
                            {isDeployingGateway ? 'DEPLOYING...' : 'DEPLOY ENVOY GATEWAY'}
                        </button>
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
        </div>
    );
};

export default ServiceView;

