import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useK8sClusters } from '../hooks/useResources';
import { Server, Cloud, Activity, Edit2 } from 'lucide-react';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import ResourceCard from '../components/ResourceCard';
import PageLayout from '../components/PageLayout';

const K8sClustersPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const { clusters, fetchClusters, loading, deleteCluster } = useK8sClusters();
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [selectedCluster, setSelectedCluster] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const filteredClusters = clusters.filter(cluster =>
        (cluster.title || cluster.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (cluster.type || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <>
            <PageLayout
                title="Kubernetes Clusters"
                description="Manage infrastructure endpoints and compute contexts."
                createConfig={{
                    title: "Add Kubernetes Cluster",
                    entityPath: "/k8s_clusters",
                    buttonText: "ADD CLUSTER",
                    initialData: { project_id: selectedProject?.id },
                    onSuccess: () => {
                        fetchClusters();
                    }
                }}
                searchQuery={searchTerm}
                onSearchChange={(e) => setSearchTerm(e.target.value)}
                searchPlaceholder="Search clusters..."
                isLoading={loading}
                isEmpty={filteredClusters.length === 0}
                emptyState={{
                    title: "No clusters found",
                    description: selectedProject ? `No Kubernetes clusters in ${selectedProject.name}.` : 'Add your first Kubernetes cluster to get started.',
                    icon: <Cloud size={48} className="text-slate-700" />
                }}
            >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredClusters.map((cluster, i) => (
                        <ResourceCard
                            key={i}
                            icon={<Cloud size={24} />}
                            title={cluster.title || cluster.name}
                            subtitle={cluster.type}
                            onEdit={() => {
                                setSelectedCluster(cluster);
                                setIsEditModalOpen(true);
                            }}
                            resourceName={cluster.name}
                            darkMode={darkMode}
                            onDelete={(name) => deleteCluster(cluster.id, name)}
                            footer={
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2 text-slate-500">
                                        <Server size={14} />
                                        <span className="text-base">? Nodes</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-slate-500">
                                        <Activity size={14} />
                                        <span className="text-base">Unknown Uptime</span>
                                    </div>
                                </div>
                            }
                        />
                    ))}
                </div>
            </PageLayout>

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
        </>
    );
};

export default K8sClustersPage;
