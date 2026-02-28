import React, { useState, useEffect } from 'react';
import {
    Server,
    Monitor,
    Trash2,
    ChevronRight,
    Edit2,
    Activity
} from 'lucide-react';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import PageLayout from '../../components/PageLayout';
import ResourceConfirmModal from '../../components/ResourceConfirmModal';
import { useNotification } from '../../providers/NotificationProvider';

const ListingView = ({ context, clustersHook, onSelectCluster }) => {
    const { darkMode } = context;
    const { clusters, loading, deleteCluster, fetchClusters, getClusterState, executeAction } = clustersHook;
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [selectedClusterForEdit, setSelectedClusterForEdit] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [clusterStates, setClusterStates] = useState({});
    const [successfullyTriggered, setSuccessfullyTriggered] = useState({});
    const { showSuccess, showError } = useNotification();

    const filteredClusters = clusters.filter(c =>
        String(c.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        String(c.description || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    useEffect(() => {
        let timer;
        const fetchStates = async () => {
            if (clusters.length === 0 || !getClusterState) return;
            const states = {};
            await Promise.all(clusters.map(async (c) => {
                try {
                    const state = await getClusterState(c.id);
                    states[c.id] = state;
                } catch (e) {
                    console.error(`Failed to fetch state for cluster ${c.id}`, e);
                }
            }));
            setClusterStates(states);
        };

        if (clusters.length > 0) {
            fetchStates();
            timer = setInterval(fetchStates, 5000);
        }

        return () => {
            if (timer) clearInterval(timer);
        };
    }, [clusters, getClusterState]);

    return (
        <React.Fragment>
            <PageLayout
                title="Kubernetes Clusters"
                description="Manage underlying infrastructure compute clusters."
                createConfig={{
                    title: "Register New Cluster",
                    entityPath: "/k8s_clusters",
                    buttonText: "REGISTER CLUSTER",
                    onSuccess: () => {
                        fetchClusters();
                    }
                }}
                searchQuery={searchTerm}
                onSearchChange={(e) => setSearchTerm(e.target.value)}
                searchPlaceholder="Search clusters by title or description..."
                isLoading={loading}
                isEmpty={filteredClusters.length === 0}
                emptyState={{
                    title: "No clusters registered",
                    description: "Register a Kubernetes cluster to start deploying infrastructure.",
                    icon: <Server size={48} className="text-slate-700" />
                }}
            >
                <div className="grid grid-cols-1 gap-4">
                    {filteredClusters.map(cluster => {
                        const state = clusterStates[cluster.id] || {};
                        const statusColor = state.status === 'online' ? 'bg-green-500' :
                            state.status === 'error' ? 'bg-red-500' :
                                state.status === 'offline' ? 'bg-slate-400' :
                                    'bg-yellow-500';

                        return (
                            <div
                                key={cluster.id}
                                className="mw-card flex items-center justify-between group cursor-pointer hover:border-blue-500/50 transition-colors"
                                onClick={() => onSelectCluster(cluster.id)}
                            >
                                <div className="flex items-center gap-6">
                                    <div className="mw-icon-box relative">
                                        <Server size={24} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
                                        <div
                                            className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white dark:border-slate-800 ${statusColor}`}
                                            title={`Cluster Status: ${state.status || 'unknown'}`}
                                        />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-3">
                                            <h4 className="text-lg font-bold text-slate-900 dark:text-white">{cluster.title}</h4>
                                            {state.k8s_version && (
                                                <span className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-500 px-2 py-0.5 rounded font-mono">
                                                    {state.k8s_version}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-base text-slate-500">{cluster.type}</p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-12">
                                    {!state.argocd_installed && state.status === 'online' && !successfullyTriggered[cluster.id] && executeAction && (
                                        <button
                                            onClick={async (e) => {
                                                e.stopPropagation();
                                                try {
                                                    const res = await executeAction(cluster.id, 'install_argocd');
                                                    showSuccess(res.message || "ArgoCD installation triggered");
                                                    setSuccessfullyTriggered(prev => ({ ...prev, [cluster.id]: true }));
                                                } catch (err) {
                                                    console.error("Failed to install ArgoCD", err);
                                                    showError("Failed to trigger ArgoCD installation");
                                                }
                                            }}
                                            className="text-[10px] font-bold bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-1.5 rounded-lg transition-all"
                                        >
                                            INSTALL ARGOCD
                                        </button>
                                    )}

                                    <div className="text-center">
                                        <p className="text-base text-slate-500 uppercase font-bold mb-1">Nodes</p>
                                        <p className="text-lg font-bold text-slate-900 dark:text-white">{state.node_count || 0}</p>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setSelectedClusterForEdit(cluster);
                                                setIsEditModalOpen(true);
                                            }}
                                            className="mw-btn-icon"
                                            title="Edit Cluster"
                                        >
                                            <Edit2 size={18} />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setSelectedClusterForEdit(cluster);
                                                setIsDeleteModalOpen(true);
                                            }}
                                            className="mw-btn-icon-danger"
                                            title="Delete Cluster"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                        <div className="w-px h-8 bg-slate-800 mx-2" />
                                        <button
                                            onClick={(e) => { e.stopPropagation(); onSelectCluster(cluster.id); }}
                                            className="p-3 text-slate-400 hover:text-white transition-all"
                                        >
                                            <ChevronRight size={20} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </PageLayout>

            <Modal
                isOpen={isEditModalOpen}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setSelectedClusterForEdit(null);
                }}
                title="Edit Cluster"
                darkMode={darkMode}
            >
                {selectedClusterForEdit && (
                    <DynamicForm
                        entityPath="/k8s_clusters"
                        mode="edit"
                        initialData={selectedClusterForEdit}
                        darkMode={darkMode}
                        onSuccess={() => {
                            setIsEditModalOpen(false);
                            setSelectedClusterForEdit(null);
                            fetchClusters();
                        }}
                        onCancel={() => {
                            setIsEditModalOpen(false);
                            setSelectedClusterForEdit(null);
                        }}
                    />
                )}
            </Modal>

            {isDeleteModalOpen && selectedClusterForEdit && (
                <ResourceConfirmModal
                    isOpen={isDeleteModalOpen}
                    onClose={() => {
                        setIsDeleteModalOpen(false);
                        setSelectedClusterForEdit(null);
                    }}
                    onConfirm={async (typedName) => {
                        await deleteCluster(selectedClusterForEdit.id, typedName);
                        setIsDeleteModalOpen(false);
                        setSelectedClusterForEdit(null);
                    }}
                    resourceName={selectedClusterForEdit.title}
                    darkMode={darkMode}
                    title="Delete Cluster"
                    message="Are you sure you want to remove this cluster? Wait, ensure that no projects are actively referencing it!"
                />
            )}
        </React.Fragment>
    );
};

export default ListingView;
