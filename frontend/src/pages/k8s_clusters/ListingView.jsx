import React, { useState } from 'react';
import { Server } from 'lucide-react';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import GenericListingView from '../../components/GenericListingView';
import { useNotification } from '../../providers/NotificationProvider';

const ListingView = ({ context, clustersHook, onSelectCluster }) => {
    const { darkMode } = context;
    const { clusters, loading, deleteCluster, fetchClusters, getClusterState, executeAction } = clustersHook;
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [selectedClusterForEdit, setSelectedClusterForEdit] = useState(null);
    const [successfullyTriggered, setSuccessfullyTriggered] = useState({});
    const { showSuccess, showError } = useNotification();

    const renderSubtitle = (cluster, state) => {
        const statusColor = state.status === 'online' ? 'bg-green-500' :
            state.status === 'error' ? 'bg-red-500' :
                state.status === 'offline' ? 'bg-slate-400' :
                    'bg-yellow-500';

        return (
            <div className="flex items-center gap-2">
                <div
                    className={`w-2.5 h-2.5 rounded-full ${statusColor}`}
                    title={`Status: ${state.status || 'unknown'}`}
                />
                <span>{cluster.type}</span>
            </div>
        );
    };

    const renderBadges = (cluster, state) => (
        state.k8s_version ? [{ text: state.k8s_version, variant: "mw-badge-neutral" }] : []
    );

    const renderActions = (cluster, state, { onDelete }) => (
        <React.Fragment>
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
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                        title="Edit Cluster"
                    >
                        {/* Using manual SVG to match existing style if lucide import is removed/changed */}
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-edit-2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
                    </button>
                    <button
                        onClick={(e) => onDelete(e, cluster)}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                        title="Delete Cluster"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-trash-2"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                    <div className="w-px h-8 bg-slate-200 dark:bg-slate-800 mx-2" />
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-chevron-right text-slate-300 dark:text-slate-600"><path d="m9 18 6-6-6-6"></path></svg>
                </div>
            </div>
        </React.Fragment>
    );

    return (
        <React.Fragment>
            <GenericListingView
                title="Kubernetes Clusters"
                description="Manage underlying infrastructure compute clusters."
                items={clusters}
                loading={loading}
                fetchItems={fetchClusters}
                deleteItem={deleteCluster}
                getItemState={getClusterState}
                onSelectItem={(cluster) => onSelectCluster(cluster.id)}
                icon={Server}
                entityPath="/k8s_clusters"
                createConfig={{
                    title: "Register New Cluster",
                    buttonText: "REGISTER CLUSTER",
                }}
                searchPlaceholder="Search clusters by title or description..."
                emptyState={{
                    title: "No clusters registered",
                    description: "Register a Kubernetes cluster to start deploying infrastructure.",
                    icon: <Server size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderBadges={renderBadges}
                renderActions={renderActions}
                deleteModalConfig={{
                    title: "Delete Cluster",
                    message: "Are you sure you want to remove this cluster? Wait, ensure that no projects are actively referencing it!"
                }}
                darkMode={darkMode}
                searchFields={["title", "description"]}
            />

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
        </React.Fragment>
    );
};

export default ListingView;
