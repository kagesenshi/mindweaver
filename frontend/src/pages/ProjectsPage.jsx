import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
    Plus,
    Briefcase,
    Monitor,
    Trash2,
    ChevronRight,
    Edit2
} from 'lucide-react';
import { useProjects } from '../hooks/useResources';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import PageLayout from '../components/PageLayout';

const ProjectsPage = () => {
    const { darkMode } = useOutletContext();
    const { projects, loading, createProject, deleteProject, fetchProjects } = useProjects();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
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
                headerActions={
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="mw-btn-primary px-4 py-2"
                    >
                        <Plus size={16} /> CREATE PROJECT
                    </button>
                }
                searchQuery={searchTerm}
                onSearchChange={(e) => setSearchTerm(e.target.value)}
                searchPlaceholder="Search projects by title or description..."
            >
                <div className="grid grid-cols-1 gap-4">
                    {loading ? (
                        <div className="py-20 flex flex-col items-center justify-center space-y-4">
                            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                            <p className="text-slate-500 text-base font-medium">Fetching projects...</p>
                        </div>
                    ) : filteredProjects.length === 0 ? (
                        <div className="py-20 text-center border-2 border-dashed border-slate-800 rounded-[40px]">
                            <Briefcase size={48} className="mx-auto text-slate-700 mb-4" />
                            <h3 className="text-lg font-bold text-slate-400">No projects found</h3>
                            <p className="text-slate-500 text-sm">Create a new project to start managing resources.</p>
                        </div>
                    ) : filteredProjects.map(proj => (
                        <div key={proj.id} className="mw-card flex items-center justify-between group">
                            <div className="flex items-center gap-6">
                                <div className="mw-icon-box">
                                    <Briefcase size={24} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
                                </div>
                                <div>
                                    <h4 className="text-lg font-bold text-slate-900 dark:text-white">{proj.title}</h4>
                                    <p className="text-sm text-slate-500">{proj.description}</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-12">
                                <div className="text-center">
                                    <p className="text-sm text-slate-500 uppercase font-bold mb-1">Resources</p>
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
                                        onClick={() => deleteProject(proj.id)}
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

                <Modal
                    isOpen={isCreateModalOpen}
                    onClose={() => setIsCreateModalOpen(false)}
                    title="Create New Project"
                    darkMode={darkMode}
                >
                    <DynamicForm
                        entityPath="/projects"
                        mode="create"
                        darkMode={darkMode}
                        onSuccess={() => {
                            setIsCreateModalOpen(false);
                            fetchProjects();
                        }}
                        onCancel={() => setIsCreateModalOpen(false)}
                    />
                </Modal>

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
                            }}
                            onCancel={() => {
                                setIsEditModalOpen(false);
                                setSelectedProject(null);
                            }}
                        />
                    )}
                </Modal>
            </PageLayout>
        </React.Fragment>
    );
};

export default ProjectsPage;
