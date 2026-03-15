import React, { useState } from 'react';
import { Briefcase } from 'lucide-react';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import GenericListingView from '../../components/GenericListingView';
import { useNotification } from '../../providers/NotificationProvider';
import { useK8sClusters } from '../../hooks/useResources';

const ListingView = ({ context, projectsHook, onSelectProject }) => {
    const { darkMode, refreshProjects } = context;
    const { projects, loading, deleteProject, fetchProjects, getProjectState } = projectsHook;
    const { clusters } = useK8sClusters();
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [selectedProjectForEdit, setSelectedProjectForEdit] = useState(null);
    const [successfullyTriggered, setSuccessfullyTriggered] = useState({});
    const { showSuccess, showError } = useNotification();

    const renderSubtitle = (proj) => (
        <span>{proj.description}</span>
    );

    const renderBadges = (proj) => (
        proj.k8s_cluster_id ? [
            {
                text: clusters.find(c => c.id === proj.k8s_cluster_id)?.title || `Cluster ID: ${proj.k8s_cluster_id}`,
                variant: "mw-badge-neutral"
            }
        ] : []
    );

    const renderActions = (proj, state, { onDelete }) => {
        const resourceCount = (state.pgsql || 0) + (state.trino || 0) + (state.spark || 0) + (state.airflow || 0);
        const cluster = state.cluster || {};

        return (
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
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-edit-2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
                    </button>
                    <button
                        onClick={(e) => onDelete(e, proj)}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                        title="Delete"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-trash-2"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                    <div className="w-px h-8 bg-slate-200 dark:bg-slate-800 mx-2" />
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-chevron-right text-slate-300 dark:text-slate-600"><path d="m9 18 6-6-6-6"></path></svg>
                </div>
            </div>
        );
    };

    return (
        <React.Fragment>
            <GenericListingView
                title="Project Registry"
                description="Tenant management and resource isolation."
                items={projects}
                loading={loading}
                fetchItems={fetchProjects}
                deleteItem={async (id, typedName) => {
                    await deleteProject(id, typedName);
                    refreshProjects?.();
                }}
                getItemState={getProjectState}
                onSelectItem={(proj) => onSelectProject(proj.id)}
                icon={Briefcase}
                entityPath="/projects"
                createConfig={{
                    title: "Create New Project",
                    buttonText: "CREATE PROJECT",
                    onSuccess: () => {
                        refreshProjects?.();
                    }
                }}
                searchPlaceholder="Search projects by title or description..."
                emptyState={{
                    title: "No projects found",
                    description: "Create a new project to start managing resources.",
                    icon: <Briefcase size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderBadges={renderBadges}
                renderActions={renderActions}
                deleteModalConfig={{
                    title: "Delete Project",
                    message: "Are you sure you want to delete this project? All associated resources will be permanently removed."
                }}
                darkMode={darkMode}
                searchFields={["title", "description"]}
            />

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
        </React.Fragment>
    );
};

export default ListingView;
