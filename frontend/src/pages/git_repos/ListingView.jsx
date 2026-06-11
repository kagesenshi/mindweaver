/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React, { useState } from 'react';
import { GitBranch, Radio, CheckCircle2, XCircle } from 'lucide-react';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import GenericListingView from '../../components/GenericListingView';
import { cn } from '../../utils/cn';
import { useNotification } from '../../providers/NotificationProvider';

const ListingView = ({
    darkMode,
    selectedProject,
    gitReposHook
}) => {
    const { repos, loading, deleteRepo, fetchRepos, testConnection } = gitReposHook;
    const { showSuccess } = useNotification();

    const [editItem, setEditItem] = useState(null);
    const [testResult, setTestResult] = useState(null);
    const [testingConnection, setTestingConnection] = useState(false);

    const runTestConnection = async (formData) => {
        setTestingConnection(true);
        setTestResult(null);
        try {
            const result = await testConnection({
                ...formData,
                repo_id: editItem?.id
            });
            const successMsg = result.message || 'Connection successful!';
            setTestResult({
                success: true,
                message: successMsg
            });
            showSuccess(successMsg);
        } catch (err) {
            setTestResult({
                success: false,
                message: err.response?.data?.detail?.msg || err.message || 'Connection failed'
            });
        } finally {
            setTestingConnection(false);
        }
    };

    const renderSubtitle = (repo) => (
        <span>{repo.url}</span>
    );

    const renderBadges = (repo) => {
        const urlLower = (repo.url || '').toLowerCase();
        const isSsh = urlLower.startsWith("git@") || urlLower.startsWith("ssh://") || urlLower.startsWith("git+ssh://");
        const hasCreds = repo.username || repo.password || repo.ssh_key_id;
        const authText = isSsh || repo.ssh_key_id ? "SSH" : (hasCreds ? "HTTP" : "NONE");
        return [
            { text: authText, variant: "mw-badge-neutral" },
        ];
    };

    return (
        <>
            <GenericListingView
                title="Git Repositories"
                description="Manage secure connections to external Git repositories for DAG and configuration synchronization."
                items={repos}
                loading={loading}
                fetchItems={fetchRepos}
                deleteItem={deleteRepo}
                onSelectItem={(repo) => setEditItem(repo)}
                onEditItem={(repo) => setEditItem(repo)}
                icon={GitBranch}
                entityPath="/git_repos"
                createConfig={{
                    title: "New Git Repository Connection",
                    buttonText: "NEW GIT CONNECTION",
                    initialData: {},
                    onClose: () => setTestResult(null),
                    renderExtraActions: (formData) => (
                        <button
                            type="button"
                            onClick={() => runTestConnection(formData)}
                            disabled={testingConnection}
                            className="mw-btn-secondary px-6 py-4"
                        >
                            {testingConnection ? <Radio className="animate-pulse" size={18} /> : <Radio size={18} />}
                            TEST CONNECTION
                        </button>
                    ),
                    extraContent: testResult && (
                        <div className={cn(
                            "p-4 rounded-xl border flex items-center gap-3 text-sm font-bold",
                            testResult.success
                                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-600"
                                : "bg-rose-500/10 border-rose-500/20 text-rose-600"
                        )}>
                            {testResult.success ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                            {testResult.message}
                        </div>
                    )
                }}
                searchPlaceholder="Search Git repositories..."
                emptyState={{
                    title: "No Git Repository connections found",
                    description: selectedProject
                        ? `No Git repository connections configured in ${selectedProject.name}.`
                        : 'Create your first Git repository connection to get started.',
                    icon: <GitBranch size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderBadges={renderBadges}
                deleteModalConfig={{
                    title: "Delete Git Repository Connection",
                    message: "Are you sure you want to delete this Git repository connection? Platforms pulling files from it will no longer be able to synchronize."
                }}
                darkMode={darkMode}
                selectedProject={selectedProject}
                searchFields={["name", "title", "url"]}
            />

            <Modal
                isOpen={!!editItem}
                onClose={() => {
                    setEditItem(null);
                    setTestResult(null);
                }}
                title="Edit Git Repository Connection"
                darkMode={darkMode}
            >
                <div className="space-y-4">
                    {testResult && (
                        <div className={cn(
                            "p-4 rounded-xl border flex items-center gap-3 text-sm font-bold",
                            testResult.success
                                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-600"
                                : "bg-rose-500/10 border-rose-500/20 text-rose-600"
                        )}
                        >
                            {testResult.success ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                            {testResult.message}
                        </div>
                    )}
                    {editItem && (
                        <DynamicForm
                            entityPath="/git_repos"
                            mode="edit"
                            darkMode={darkMode}
                            initialData={editItem}
                            onSuccess={() => {
                                fetchRepos();
                                setEditItem(null);
                            }}
                            onCancel={() => setEditItem(null)}
                            renderExtraActions={(formData) => (
                                <button
                                    type="button"
                                    onClick={() => runTestConnection(formData)}
                                    disabled={testingConnection}
                                    className="mw-btn-secondary px-6 py-4"
                                >
                                    {testingConnection ? <Radio className="animate-pulse" size={18} /> : <Radio size={18} />}
                                    TEST CONNECTION
                                </button>
                            )}
                        />
                    )}
                </div>
            </Modal >
        </>
    );
};

export default ListingView;
