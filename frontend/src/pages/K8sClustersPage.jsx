import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useK8sClusters } from '../hooks/useResources';
import { Server, Cloud, Activity, Plus, Edit2 } from 'lucide-react';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import ResourceCard from '../components/ResourceCard';

const K8sClustersPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const { clusters, fetchClusters } = useK8sClusters();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [selectedCluster, setSelectedCluster] = useState(null);

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="mw-page-header">
                <div>
                    <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white uppercase">Kubernetes Clusters</h2>
                    <p className="text-slate-500 mt-1 text-base">Manage infrastructure endpoints and compute contexts.</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="mw-btn-primary px-4 py-2"
                >
                    <Plus size={16} /> ADD CLUSTER
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {clusters.map((cluster, i) => (
                    <ResourceCard
                        key={i}
                        icon={<Cloud size={24} />}
                        title={cluster.title || cluster.name}
                        subtitle={cluster.type}
                        status="active"
                        onEdit={() => {
                            setSelectedCluster(cluster);
                            setIsEditModalOpen(true);
                        }}
                        footer={
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2 text-slate-500">
                                    <Server size={14} />
                                    <span className="text-sm">? Nodes</span>
                                </div>
                                <div className="flex items-center gap-2 text-slate-500">
                                    <Activity size={14} />
                                    <span className="text-sm">Unknown Uptime</span>
                                </div>
                            </div>
                        }
                    />
                ))}
            </div>

            <Modal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                title="Add Kubernetes Cluster"
                darkMode={darkMode}
            >
                <DynamicForm
                    entityPath="/k8s_clusters"
                    mode="create"
                    darkMode={darkMode}
                    initialData={{ project_id: selectedProject?.id }}
                    onSuccess={() => {
                        fetchClusters();
                        setIsCreateModalOpen(false);
                    }}
                    onCancel={() => setIsCreateModalOpen(false)}
                />
            </Modal>

            <Modal
                isOpen={isEditModalOpen}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setSelectedCluster(null);
                }}
                title="Edit Kubernetes Cluster"
                darkMode={darkMode}
            >
                {selectedCluster && (
                    <DynamicForm
                        entityPath="/k8s_clusters"
                        mode="edit"
                        initialData={selectedCluster}
                        darkMode={darkMode}
                        onSuccess={() => {
                            fetchClusters();
                            setIsEditModalOpen(false);
                            setSelectedCluster(null);
                        }}
                        onCancel={() => {
                            setIsEditModalOpen(false);
                            setSelectedCluster(null);
                        }}
                    />
                )}
            </Modal>
        </div>
    );
};

export default K8sClustersPage;
