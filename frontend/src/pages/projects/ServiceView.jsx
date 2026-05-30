import React, { useState, useEffect } from 'react';
import {
    Briefcase, Database, Server, Activity, ArrowLeft, Monitor, Users, UserPlus, Edit, Trash2, Shield, RefreshCw
} from 'lucide-react';
import { useProjectLocalUsers } from '../../hooks/useResources';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import ResourceConfirmModal from '../../components/ResourceConfirmModal';
import { useNotification } from '../../providers/NotificationProvider';

const ServiceView = ({
    context,
    selectedProjectId,
    selectedProject,
    onBack,
    projectsHook
}) => {
    const { darkMode } = context || {};
    const { getProjectState } = projectsHook;
    const [projectState, setProjectState] = useState(null);
    const { showSuccess, showError } = useNotification();

    const localUsersHook = useProjectLocalUsers();
    const { items: localUsers, loading: loadingUsers, fetchItems: fetchUsers, deleteItem: deleteUser } = localUsersHook;

    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [deleteItem, setDeleteItem] = useState(null);
    const [isInstallingDex, setIsInstallingDex] = useState(false);

    useEffect(() => {
        let timer;
        if (selectedProjectId) {
            getProjectState(selectedProjectId).then(setProjectState);

            timer = setInterval(() => {
                getProjectState(selectedProjectId).then(setProjectState);
            }, 10000);
        } else {
            Promise.resolve().then(() => setProjectState(null));
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [selectedProjectId, getProjectState]);

    const projectUsers = localUsers.filter(u => u.project_id === selectedProjectId);

    const handleInstallDex = async () => {
        setIsInstallingDex(true);
        try {
            await projectsHook.executeAction(selectedProjectId, 'install_dex');
            showSuccess("Dex installation triggered for this project");
            const newState = await getProjectState(selectedProjectId);
            setProjectState(newState);
        } catch (e) {
            console.error(e);
            showError("Failed to trigger Dex installation");
        } finally {
            setIsInstallingDex(false);
        }
    };

    const resourceCards = [
        {
            name: "PostgreSQL",
            icon: Database,
            count: projectState?.pgsql || 0,
            color: "text-blue-500",
            bg: "bg-blue-500/10"
        },
        {
            name: "Trino",
            icon: Server,
            count: projectState?.trino || 0,
            color: "text-purple-500",
            bg: "bg-purple-500/10"
        },
        {
            name: "Spark",
            icon: Activity,
            count: projectState?.spark || 0,
            color: "text-orange-500",
            bg: "bg-orange-500/10"
        },
        {
            name: "Airflow",
            icon: Activity,
            count: projectState?.airflow || 0,
            color: "text-teal-500",
            bg: "bg-teal-500/10"
        }
    ];

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="mw-page-header">
                <div className="flex gap-4 items-center">
                    <button
                        onClick={onBack}
                        className="p-3 text-slate-400 hover:text-slate-900 dark:hover:text-white transition-all bg-slate-100 dark:bg-slate-800 rounded-xl"
                    >
                        <ArrowLeft size={24} />
                    </button>
                    <div className="mw-icon-box w-16 h-16 text-indigo-400">
                        <Monitor size={32} />
                    </div>
                    <div>
                        <div className="flex items-center gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{selectedProject.title} Fleet Overview</h2>
                        </div>
                        <div className="flex items-center gap-4 mt-2">
                            <span className="flex items-center gap-1.5 text-sm text-slate-400">
                                Project ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedProject.id}</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                {resourceCards.map((card, i) => {
                    const Icon = card.icon;
                    return (
                        <div key={i} className="mw-card p-6 flex flex-col gap-4">
                            <div className="flex items-center gap-4">
                                <div className={`p-4 rounded-xl ${card.bg} ${card.color}`}>
                                    <Icon size={24} />
                                </div>
                                <h3 className="text-xl font-bold text-slate-900 dark:text-white uppercase tracking-wider">{card.name}</h3>
                            </div>
                            <div className="mt-2 text-center bg-slate-50 dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                                <p className="text-4xl font-bold text-slate-900 dark:text-white mb-1">{card.count}</p>
                                <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Instances Deployed</p>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Dex OIDC Integration */}
            <div className="mw-card p-8 space-y-6 animate-in slide-in-from-bottom duration-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="mw-icon-box text-indigo-500">
                            <Shield size={24} />
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Dex OIDC Integration</h3>
                            <p className="text-sm text-slate-500 font-medium uppercase tracking-tight">Federated identity provider for project components</p>
                        </div>
                    </div>
                    {projectState?.dex_installed ? (
                        <div className="flex items-center gap-3">
                            <span className="text-sm font-bold bg-green-500/10 text-green-500 px-3 py-1.5 rounded-xl border border-green-500/20 flex items-center gap-1.5">
                                <span className="w-2 h-2 rounded-full bg-green-500" />
                                {projectState.dex_version || "ACTIVE"}
                            </span>
                            <button
                                onClick={handleInstallDex}
                                disabled={isInstallingDex}
                                className="mw-btn-secondary px-6 py-2.5 flex items-center gap-2"
                            >
                                {isInstallingDex ? <RefreshCw size={16} className="animate-spin" /> : <RefreshCw size={16} />}
                                UPDATE DEX
                            </button>
                        </div>
                    ) : (
                        <button
                            onClick={handleInstallDex}
                            disabled={isInstallingDex}
                            className="mw-btn-primary px-6 py-2.5 flex items-center gap-2"
                        >
                            {isInstallingDex ? <RefreshCw size={16} className="animate-spin" /> : <Shield size={16} />}
                            {isInstallingDex ? 'INSTALLING...' : 'INSTALL DEX OIDC'}
                        </button>
                    )}
                </div>
            </div>

            {/* Project Local Users Management */}
            <div className="mw-card p-8 space-y-8 animate-in slide-in-from-bottom duration-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="mw-icon-box text-indigo-500">
                            <Users size={24} />
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Local User Management</h3>
                            <p className="text-sm text-slate-500 font-medium uppercase tracking-tight">Manage project-scoped credentials for OIDC integration</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setIsCreateOpen(true)}
                        className="mw-btn-primary px-6 py-2.5 flex items-center gap-2"
                    >
                        <UserPlus size={16} />
                        ADD LOCAL USER
                    </button>
                </div>

                {loadingUsers ? (
                    <div className="text-center py-8 text-slate-500">
                        Loading users...
                    </div>
                ) : projectUsers.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                        No local users configured for this project.
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-slate-200 dark:border-slate-800 text-xs font-bold uppercase tracking-widest text-slate-400">
                                    <th className="py-4 px-6">Username</th>
                                    <th className="py-4 px-6">Email Address</th>
                                    <th className="py-4 px-6 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {projectUsers.map(user => (
                                    <tr key={user.id} className="border-b border-slate-100 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-900/20 transition-colors">
                                        <td className="py-4 px-6 font-semibold text-slate-900 dark:text-white">{user.username}</td>
                                        <td className="py-4 px-6 text-slate-500 dark:text-slate-400">{user.email}</td>
                                        <td className="py-4 px-6 text-right flex justify-end gap-2">
                                            <button
                                                onClick={() => setEditItem(user)}
                                                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400 hover:text-blue-500 transition-colors"
                                                title="Edit User"
                                            >
                                                <Edit size={16} />
                                            </button>
                                            <button
                                                onClick={() => setDeleteItem(user)}
                                                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400 hover:text-rose-500 transition-colors"
                                                title="Delete User"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Create Modal */}
            <Modal
                isOpen={isCreateOpen}
                onClose={() => setIsCreateOpen(false)}
                title="Add Local User"
                darkMode={darkMode}
            >
                <DynamicForm
                    entityPath="/project-local-users"
                    mode="create"
                    initialData={{ project_id: selectedProjectId }}
                    darkMode={darkMode}
                    onSuccess={async () => {
                        setIsCreateOpen(false);
                        await fetchUsers();
                    }}
                    onCancel={() => setIsCreateOpen(false)}
                />
            </Modal>

            {/* Edit Modal */}
            <Modal
                isOpen={!!editItem}
                onClose={() => setEditItem(null)}
                title="Edit Local User"
                darkMode={darkMode}
            >
                {editItem && (
                    <DynamicForm
                        entityPath="/project-local-users"
                        mode="edit"
                        initialData={editItem}
                        darkMode={darkMode}
                        onSuccess={async () => {
                            setEditItem(null);
                            await fetchUsers();
                        }}
                        onCancel={() => setEditItem(null)}
                    />
                )}
            </Modal>

            {/* Delete Confirmation Modal */}
            {deleteItem && (
                <ResourceConfirmModal
                    isOpen={!!deleteItem}
                    onClose={() => setDeleteItem(null)}
                    onConfirm={async (confirmName) => {
                        await deleteUser(deleteItem.id, confirmName);
                        await fetchUsers();
                    }}
                    resourceName={deleteItem.username}
                    title="Delete Local User"
                    message="Are you sure you want to delete this local user?"
                    darkMode={darkMode}
                />
            )}
        </div>
    );
};

export default ServiceView;

