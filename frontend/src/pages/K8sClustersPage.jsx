import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useK8sClusters } from '../hooks/useResources';
import { Server, Cloud, Activity, Plus, Edit2 } from 'lucide-react';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';

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
                    <div key={i} className="mw-card group">
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-4">
                                <div className="mw-icon-box p-3 text-indigo-400">
                                    <Cloud size={24} />
                                </div>
                                <div>
                                    <h4 className="text-lg font-bold text-slate-900 dark:text-white uppercase">{cluster.title || cluster.name}</h4>
                                    <p className="text-sm text-slate-500 font-mono uppercase mt-0.5">{cluster.type}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="mw-badge-success">ACTIVE</div>
                                <button
                                    onClick={() => {
                                        setSelectedCluster(cluster);
                                        setIsEditModalOpen(true);
                                    }}
                                    className="mw-btn-icon"
                                    title="Edit Cluster"
                                >
                                    <Edit2 size={16} />
                                </button>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 pt-4 border-t border-slate-800/50">
                            <div className="flex items-center gap-2 text-slate-500"><Server size={14} /><span className="text-sm">? Nodes</span></div>
                            <div className="flex items-center gap-2 text-slate-500"><Activity size={14} /><span className="text-sm">Unknown Uptime</span></div>
                        </div>
                    </div>
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
