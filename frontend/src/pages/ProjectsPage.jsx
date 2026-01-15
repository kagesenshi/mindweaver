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

    const cardBg = darkMode ? "bg-slate-900/40 border-slate-800" : "bg-white border-slate-200 shadow-sm";
    const textColor = darkMode ? "text-white" : "text-slate-900";

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-end justify-between border-b pb-6 border-slate-800/50">
                <div>
                    <h2 className={cn("text-3xl font-bold tracking-tight", textColor)}>Project Registry</h2>
                    <p className="text-slate-500 mt-1">Tenant management and resource isolation.</p>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-lg shadow-lg shadow-blue-600/20 hover:bg-blue-500 transition-all font-sans"
                >
                    <Plus size={16} /> CREATE PROJECT
                </button>
            </div>

            <div className="flex items-center gap-4 mb-8">
                <div className={cn(
                    "flex-1 relative border rounded-xl px-4 py-2 flex items-center gap-3",
                    darkMode ? 'bg-slate-900/50 border-slate-800' : 'bg-white border-slate-200'
                )}>
                    <Search size={18} className="text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search projects by title or description..."
                        className="bg-transparent text-sm focus:outline-none w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {loading ? (
                    <div className="py-20 flex flex-col items-center justify-center space-y-4">
                        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        <p className="text-slate-500 text-sm font-medium">Fetching projects...</p>
                    </div>
                ) : filteredProjects.length === 0 ? (
                    <div className="py-20 text-center border-2 border-dashed border-slate-800 rounded-[40px]">
                        <Briefcase size={48} className="mx-auto text-slate-700 mb-4" />
                        <h3 className="text-lg font-bold text-slate-400">No projects found</h3>
                        <p className="text-slate-500 text-sm">Create a new project to start managing resources.</p>
                    </div>
                ) : filteredProjects.map(proj => (
                    <div key={proj.id} className={cn(
                        "border rounded-[32px] p-6 flex items-center justify-between group transition-all hover:border-blue-500/30",
                        cardBg
                    )}>
                        <div className="flex items-center gap-6">
                            <div className={cn(
                                "w-12 h-12 rounded-2xl flex items-center justify-center text-slate-400 group-hover:text-blue-500 transition-colors",
                                darkMode ? 'bg-slate-800' : 'bg-slate-100'
                            )}>
                                <Briefcase size={24} />
                            </div>
                            <div>
                                <h4 className={cn("text-lg font-bold", textColor)}>{proj.title}</h4>
                                <p className="text-sm text-slate-500">{proj.description}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-12">
                            <div className="text-center">
                                <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Resources</p>
                                <p className={cn("text-xl font-bold", textColor)}>3</p>
                            </div>

                            <div className="flex items-center gap-2">
                                <button
                                    className="p-3 text-slate-500 hover:text-blue-500 hover:bg-blue-500/10 rounded-xl transition-all"
                                    title="View Projects Fleet"
                                >
                                    <Monitor size={18} />
                                </button>
                                <button
                                    onClick={() => {
                                        setSelectedProject(proj);
                                        setIsEditModalOpen(true);
                                    }}
                                    className="p-3 text-slate-500 hover:text-blue-500 hover:bg-blue-500/10 rounded-xl transition-all"
                                    title="Edit Project"
                                >
                                    <Edit2 size={18} />
                                </button>
                                <button
                                    onClick={() => deleteProject(proj.id)}
                                    className="p-3 text-slate-500 hover:text-rose-500 hover:bg-rose-500/10 rounded-xl transition-all"
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
