import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
    Plus,
    Briefcase,
    Monitor,
    Trash2,
    ExternalLink,
    ChevronRight,
    Search,
    Edit2
} from 'lucide-react';
import { useProjects } from '../hooks/useResources';
import { cn } from '../utils/cn';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';

const ProjectsPage = () => {
    const { darkMode } = useOutletContext();
    const { projects, loading, createProject, deleteProject, fetchProjects } = useProjects();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [selectedProject, setSelectedProject] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const filteredProjects = projects.filter(p =>
        p.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.description?.toLowerCase().includes(searchTerm.toLowerCase())
    );


    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="mw-page-header">
                <div>
                    <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white uppercase">Project Registry</h2>
                    <p className="text-slate-500 mt-1 text-base">Tenant management and resource isolation.</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="mw-btn-primary px-4 py-2"
                >
                    <Plus size={16} /> CREATE PROJECT
                </button>
            </div>

            <div className="flex items-center gap-4 mb-8">
                <div className="mw-search-box flex-1">
                    <Search size={18} className="text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search projects by title or description..."
                        className="bg-transparent text-base focus:outline-none w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

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
                                <h4 className="text-lg font-bold text-slate-900 dark:text-white uppercase">{proj.title}</h4>
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
        </div>
    );
};

export default ProjectsPage;
