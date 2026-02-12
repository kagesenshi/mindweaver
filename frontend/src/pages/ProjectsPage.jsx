import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
    Briefcase,
    Monitor,
    Trash2,
    ChevronRight,
    Edit2
} from 'lucide-react';
import { useProjects } from '../hooks/useResources';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import PageLayout from '../components/PageLayout';
import ResourceConfirmModal from '../components/ResourceConfirmModal';

const ProjectsPage = () => {
    const { darkMode, refreshProjects } = useOutletContext();
    const { projects, loading, deleteProject, fetchProjects } = useProjects();
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [selectedProject, setSelectedProject] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const filteredProjects = projects.filter(p =>
        String(p.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        String(p.description || '').toLowerCase().includes(searchTerm.toLowerCase())
    );


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
                    {filteredProjects.map(proj => (
                        <div key={proj.id} className="mw-card flex items-center justify-between group">
                            <div className="flex items-center gap-6">
                                <div className="mw-icon-box">
                                    <Briefcase size={24} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
                                </div>
                                <div>
                                    <h4 className="text-lg font-bold text-slate-900 dark:text-white">{proj.title}</h4>
                                    <p className="text-base text-slate-500">{proj.description}</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-12">
                                <div className="text-center">
                                    <p className="text-base text-slate-500 uppercase font-bold mb-1">Resources</p>
                                    <p className="text-lg font-bold text-slate-900 dark:text-white">3</p>
                                </div>

                                <div className="flex items-center gap-2">
                                    <button
                                        className="mw-btn-icon"
                                        title="View Projects Fleet"
                                    >
                                        <Monitor size={18} />
                                    </button>
                                    <button
                                        onClick={() => {
                                            setSelectedProject(proj);
                                            setIsEditModalOpen(true);
                                        }}
                                        className="mw-btn-icon"
                                        title="Edit Project"
                                    >
                                        <Edit2 size={18} />
                                    </button>
                                    <button
                                        onClick={() => {
                                            setSelectedProject(proj);
                                            setIsDeleteModalOpen(true);
                                        }}
                                        className="mw-btn-icon-danger"
                                        title="Delete Project"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                    <div className="w-px h-8 bg-slate-800 mx-2" />
                                    <button className="p-3 text-slate-400 hover:text-white transition-all">
                                        <ChevronRight size={20} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </PageLayout>

            <Modal
                isOpen={isEditModalOpen}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setSelectedProject(null);
                }}
                title="Edit Project"
                darkMode={darkMode}
            >
                {selectedProject && (
                    <DynamicForm
                        entityPath="/projects"
                        mode="edit"
                        initialData={selectedProject}
                        darkMode={darkMode}
                        onSuccess={() => {
                            setIsEditModalOpen(false);
                            setSelectedProject(null);
                            fetchProjects();
                            refreshProjects?.();
                        }}
                        onCancel={() => {
                            setIsEditModalOpen(false);
                            setSelectedProject(null);
                        }}
                    />
                )}
            </Modal>

            {isDeleteModalOpen && selectedProject && (
                <ResourceConfirmModal
                    isOpen={isDeleteModalOpen}
                    onClose={() => {
                        setIsDeleteModalOpen(false);
                        setSelectedProject(null);
                    }}
                    onConfirm={async (typedName) => {
                        await deleteProject(selectedProject.id, typedName);
                        setIsDeleteModalOpen(false);
                        setSelectedProject(null);
                        refreshProjects?.();
                    }}
                    resourceName={selectedProject.title}
                    darkMode={darkMode}
                    title="Delete Project"
                    message="Are you sure you want to delete this project? All associated resources will be permanently removed."
                />
            )}
        </React.Fragment>
    );
};

export default ProjectsPage;
