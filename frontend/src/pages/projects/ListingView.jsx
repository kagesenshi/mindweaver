import React, { useState, useEffect } from 'react';
import {
    Briefcase,
    Trash2,
    ChevronRight,
    Edit2,
    Server
} from 'lucide-react';
import ListingItem from '../../components/ListingItem';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import PageLayout from '../../components/PageLayout';
import ResourceConfirmModal from '../../components/ResourceConfirmModal';
import { useNotification } from '../../providers/NotificationProvider';
import { useK8sClusters } from '../../hooks/useResources';

const ListingView = ({ context, projectsHook, onSelectProject }) => {
    const { darkMode, refreshProjects } = context;
    const { projects, loading, deleteProject, fetchProjects, getProjectState } = projectsHook;
    const { clusters } = useK8sClusters();
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [selectedProjectForEdit, setSelectedProjectForEdit] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [projectStates, setProjectStates] = useState({});
    const [successfullyTriggered, setSuccessfullyTriggered] = useState({});
    const { showSuccess, showError } = useNotification();

    const filteredProjects = projects.filter(p =>
        String(p.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        String(p.description || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    useEffect(() => {
        let timer;
        const fetchStates = async () => {
            if (projects.length === 0) return;
            const states = {};
            await Promise.all(projects.map(async (p) => {
                try {
                    const state = await getProjectState(p.id);
                    states[p.id] = state;
                } catch (e) {
                    console.error(`Failed to fetch state for project ${p.id}`, e);
                }
            }));
            setProjectStates(states);
        };

        if (projects.length > 0) {
            fetchStates();
            timer = setInterval(fetchStates, 5000);
        }

        return () => {
            if (timer) clearInterval(timer);
        };
    }, [projects, getProjectState]);

    return (
        <React.Fragment>
            <PageLayout
                title="Project Registry"
                description="Tenant management and resource isolation."
                createConfig={{
                    title: "Create New Project",
                    entityPath: "/projects",
                    buttonText: "CREATE PROJECT",
                    onSuccess: () => {
                        fetchProjects();
                        refreshProjects?.();
                    }
                }}
                searchQuery={searchTerm}
                onSearchChange={(e) => setSearchTerm(e.target.value)}
                searchPlaceholder="Search projects by title or description..."
                isLoading={loading}
                isEmpty={filteredProjects.length === 0}
                emptyState={{
                    title: "No projects found",
                    description: "Create a new project to start managing resources.",
                    icon: <Briefcase size={48} className="text-slate-700" />
                }}
            >
                <div className="grid grid-cols-1 gap-4">
                    {filteredProjects.map(proj => {
                        const state = projectStates[proj.id] || {};
                        const resourceCount = (state.pgsql || 0) + (state.trino || 0) + (state.spark || 0) + (state.airflow || 0);
                        const cluster = state.cluster || {};

                        return (
                            <ListingItem
                                key={proj.id}
                                icon={Briefcase}
                                title={proj.title}
                                badges={proj.k8s_cluster_id ? [
                                    {
                                        text: clusters.find(c => c.id === proj.k8s_cluster_id)?.title || `Cluster ID: ${proj.k8s_cluster_id}`,
                                        variant: "mw-badge-neutral"
                                    }
                                ] : []}
                                subtitle={proj.description}
                                onClick={() => onSelectProject(proj.id)}
                                actions={
                                    <div className="flex items-center gap-12">
                                        {!cluster.argocd_installed && cluster.status === 'online' && !successfullyTriggered[proj.id] && (
                                            <button
                                                onClick={async (e) => {
                                                    e.stopPropagation();
                                                    try {
                                                        const res = await projectsHook.executeAction(proj.id, 'install_argocd');
                                                        showSuccess(res.message || "ArgoCD installation triggered");
                                                        setSuccessfullyTriggered(prev => ({ ...prev, [proj.id]: true }));
                                                        refreshProjects?.();
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
                                            <p className="text-base text-slate-500 uppercase font-bold mb-1">Resources</p>
                                            <p className="text-lg font-bold text-slate-900 dark:text-white">{resourceCount}</p>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setSelectedProjectForEdit(proj);
                                                    setIsEditModalOpen(true);
                                                }}
                                                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                                                title="Edit"
                                            >
                                                <Edit2 size={18} />
                                            </button>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setSelectedProjectForEdit(proj);
                                                    setIsDeleteModalOpen(true);
                                                }}
                                                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                                                title="Delete"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                            <div className="w-px h-8 bg-slate-200 dark:bg-slate-800 mx-2" />
                                            <ChevronRight className="w-5 h-5 text-slate-300 dark:text-slate-600" />
                                        </div>
                                    </div>
                                }
                            />
                        );
                    })}

                </div>
            </PageLayout>

            <Modal
                isOpen={isEditModalOpen}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setSelectedProjectForEdit(null);
                }}
                title="Edit Project"
                darkMode={darkMode}
            >
                {selectedProjectForEdit && (
                    <DynamicForm
                        entityPath="/projects"
                        mode="edit"
                        initialData={selectedProjectForEdit}
                        darkMode={darkMode}
                        onSuccess={() => {
                            setIsEditModalOpen(false);
                            setSelectedProjectForEdit(null);
                            fetchProjects();
                            refreshProjects?.();
                        }}
                        onCancel={() => {
                            setIsEditModalOpen(false);
                            setSelectedProjectForEdit(null);
                        }}
                    />
                )}
            </Modal>

            {isDeleteModalOpen && selectedProjectForEdit && (
                <ResourceConfirmModal
                    isOpen={isDeleteModalOpen}
                    onClose={() => {
                        setIsDeleteModalOpen(false);
                        setSelectedProjectForEdit(null);
                    }}
                    onConfirm={async (typedName) => {
                        await deleteProject(selectedProjectForEdit.id, typedName);
                        setIsDeleteModalOpen(false);
                        setSelectedProjectForEdit(null);
                        refreshProjects?.();
                    }}
                    resourceName={selectedProjectForEdit.title}
                    darkMode={darkMode}
                    title="Delete Project"
                    message="Are you sure you want to delete this project? All associated resources will be permanently removed."
                />
            )}
        </React.Fragment>
    );
};

export default ListingView;
