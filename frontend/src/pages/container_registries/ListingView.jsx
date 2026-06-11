/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React, { useState } from 'react';
import { Layers, Radio, CheckCircle2, XCircle } from 'lucide-react';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import GenericListingView from '../../components/GenericListingView';
import { cn } from '../../utils/cn';
import { useNotification } from '../../providers/NotificationProvider';

const ListingView = ({
    darkMode,
    selectedProject,
    registriesHook
}) => {
    const { registries, loading, deleteRegistry, fetchRegistries, testConnection } = registriesHook;
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
                registry_id: editItem?.id
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

    const renderSubtitle = (reg) => (
        <span>{reg.url}</span>
    );

    const renderBadges = (reg) => {
        return [
            { text: reg.username ? "AUTH" : "ANONYMOUS", variant: "mw-badge-neutral" },
        ];
    };

    return (
        <>
            <GenericListingView
                title="Container Registry"
                description="Manage secure credentials and tokens for pulling container images from external OCI/Docker registries."
                items={registries}
                loading={loading}
                fetchItems={fetchRegistries}
                deleteItem={deleteRegistry}
                onSelectItem={(reg) => setEditItem(reg)}
                onEditItem={(reg) => setEditItem(reg)}
                icon={Layers}
                entityPath="/container_registries"
                createConfig={{
                    title: "New Container Registry Connection",
                    buttonText: "NEW REGISTRY CONNECTION",
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
                searchPlaceholder="Search container registries..."
                emptyState={{
                    title: "No Container Registry connections found",
                    description: selectedProject
                        ? `No Container Registry connections configured in ${selectedProject.name}.`
                        : 'Create your first Container Registry connection to get started.',
                    icon: <Layers size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderBadges={renderBadges}
                deleteModalConfig={{
                    title: "Delete Container Registry Connection",
                    message: "Are you sure you want to delete this Container Registry connection? Applications using images from this registry might fail to pull updates."
                }}
                darkMode={darkMode}
                selectedProject={selectedProject}
                searchFields={["name", "title", "url", "username"]}
            />

            <Modal
                isOpen={!!editItem}
                onClose={() => {
                    setEditItem(null);
                    setTestResult(null);
                }}
                title="Edit Container Registry Connection"
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
                            entityPath="/container_registries"
                            mode="edit"
                            darkMode={darkMode}
                            initialData={editItem}
                            onSuccess={() => {
                                fetchRegistries();
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
