import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Server, Cloud, Activity, Plus } from 'lucide-react';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';

const K8sClustersPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const textColor = darkMode ? "text-white" : "text-slate-900";
    const cardBg = darkMode ? "bg-slate-900/40 border-slate-800" : "bg-white border-slate-200 shadow-sm";

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-end justify-between border-b pb-6 border-slate-800/50">
                <div>
                    <h2 className={cn("text-3xl font-bold tracking-tight", textColor)}>Kubernetes Clusters</h2>
                    <p className="text-slate-500 mt-1">Manage infrastructure endpoints and compute contexts.</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-lg shadow-lg hover:bg-blue-500 transition-all font-sans"
                >
                    <Plus size={16} /> ADD CLUSTER
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                    { name: 'Production GKE', region: 'us-east1-b', status: 'healthy', nodes: 12 },
                    { name: 'Staging EKS', region: 'eu-west-1', status: 'healthy', nodes: 3 }
                ].map((cluster, i) => (
                    <div key={i} className={cn("border rounded-[32px] p-6 transition-all group hover:border-blue-500/30", cardBg)}>
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-4">
                                <div className={cn("p-3 rounded-2xl", darkMode ? 'bg-slate-800 text-indigo-400' : 'bg-slate-100 text-indigo-600')}>
                                    <Cloud size={24} />
                                </div>
                                <div>
                                    <h4 className={cn("font-bold", textColor)}>{cluster.name}</h4>
                                    <p className="text-[10px] text-slate-500 font-mono uppercase mt-0.5">{cluster.region}</p>
                                </div>
                            </div>
                            <div className="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-emerald-500/10 text-emerald-500 border-emerald-500/20">HEALTHY</div>
                        </div>
                        <div className="flex items-center gap-4 pt-4 border-t border-slate-800/50">
                            <div className="flex items-center gap-2 text-slate-500"><Server size={14} /><span className="text-xs">{cluster.nodes} Nodes</span></div>
                            <div className="flex items-center gap-2 text-slate-500"><Activity size={14} /><span className="text-xs">99.9% Uptime</span></div>
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
                        setIsCreateModalOpen(false);
                    }}
                    onCancel={() => setIsCreateModalOpen(false)}
                />
            </Modal>
        </div>
    );
};

export default K8sClustersPage;
