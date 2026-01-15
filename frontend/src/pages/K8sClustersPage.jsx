import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useK8sClusters } from '../hooks/useResources';
import { Server, Cloud, Activity, Plus, Edit2 } from 'lucide-react';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import ResourceCard from '../components/ResourceCard';
import PageLayout from '../components/PageLayout';

const K8sClustersPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const { clusters, fetchClusters } = useK8sClusters();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [selectedCluster, setSelectedCluster] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const filteredClusters = clusters.filter(cluster =>
        (cluster.title || cluster.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (cluster.type || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <PageLayout
            title="Kubernetes Clusters"
            description="Manage infrastructure endpoints and compute contexts."
            headerActions={
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="mw-btn-primary px-4 py-2"
                >
                    <Plus size={16} /> ADD CLUSTER
                </button>
            }
            searchQuery={searchTerm}
            onSearchChange={(e) => setSearchTerm(e.target.value)}
            searchPlaceholder="Search clusters..."
        >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredClusters.map((cluster, i) => (
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
        </PageLayout>
    );
};

export default K8sClustersPage;
