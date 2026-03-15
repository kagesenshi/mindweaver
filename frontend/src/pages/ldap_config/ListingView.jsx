import React, { useState } from 'react';
import { BookA, Radio, CheckCircle2, XCircle } from 'lucide-react';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import GenericListingView from '../../components/GenericListingView';
import { cn } from '../../utils/cn';
import { useNotification } from '../../providers/NotificationProvider';

const ListingView = ({
    darkMode,
    selectedProject,
    ldapConfigsHook
}) => {
    const { configs, loading, deleteConfig, fetchConfigs, testConnection } = ldapConfigsHook;
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
                storage_id: editItem?.id
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

    const renderSubtitle = (config) => (
        <span>{config.server_url}</span>
    );

    const renderBadges = (config) => ([
        { text: config.server_url?.startsWith('ldaps') ? 'LDAPS' : 'LDAP', variant: "mw-badge-neutral" },
    ]);

    return (
        <>
            <GenericListingView
                title="LDAP Configuration"
                description="Manage LDAP directory connections for user authentication and authorization across platforms."
                items={configs}
                loading={loading}
                fetchItems={fetchConfigs}
                deleteItem={deleteConfig}
                onSelectItem={(config) => setEditItem(config)}
                onEditItem={(config) => setEditItem(config)}
                icon={BookA}
                entityPath="/ldap_configs"
                createConfig={{
                    title: "New LDAP Config",
                    buttonText: "NEW CONFIG",
                    initialData: {
                        verify_ssl: true
                    },
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
                searchPlaceholder="Search LDAP configs..."
                emptyState={{
                    title: "No LDAP configurations found",
                    description: selectedProject
                        ? `No LDAP configurations found in ${selectedProject.name}.`
                        : 'Create your first LDAP configuration to get started.',
                    icon: <BookA size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderBadges={renderBadges}
                deleteModalConfig={{
                    title: "Delete LDAP Configuration",
                    message: "Are you sure you want to delete this LDAP configuration? This may affect authentication for projects using it."
                }}
                darkMode={darkMode}
                selectedProject={selectedProject}
                searchFields={["name", "title", "server_url"]}
            />

            <Modal
                isOpen={!!editItem}
                onClose={() => {
                    setEditItem(null);
                    setTestResult(null);
                }}
                title="Edit LDAP Config"
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
                            entityPath="/ldap_configs"
                            mode="edit"
                            darkMode={darkMode}
                            initialData={editItem}
                            onSuccess={() => {
                                fetchConfigs();
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
