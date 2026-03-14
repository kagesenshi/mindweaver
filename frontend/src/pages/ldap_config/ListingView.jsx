import React, { useState } from 'react';
import { BookA, Edit2, Trash2, ChevronRight, Radio, CheckCircle2, XCircle } from 'lucide-react';
import ListingItem from '../../components/ListingItem';
import PageLayout from '../../components/PageLayout';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import { cn } from '../../utils/cn';
import { useNotification } from '../../providers/NotificationProvider';

const ListingView = ({
    darkMode,
    selectedProject,
    ldapConfigsHook
}) => {
    const { configs, loading, deleteConfig, fetchConfigs, testConnection } = ldapConfigsHook;
    const { showSuccess } = useNotification();

    const [searchTerm, setSearchTerm] = useState('');
    const [editItem, setEditItem] = useState(null);
    const [testResult, setTestResult] = useState(null);
    const [testingConnection, setTestingConnection] = useState(false);

    const filteredConfigs = configs.filter(c => {
        const matchesProject = !selectedProject || c.project_id === selectedProject.id;
        const matchesSearch = (c.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (c.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (c.server_url || '').toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && matchesSearch;
    });

    const handleCreate = () => {
        fetchConfigs();
    };

    const handleUpdate = () => {
        fetchConfigs();
        setEditItem(null);
    };

    const handleDelete = async (id, confirmName) => {
        await deleteConfig(id, confirmName);
    };

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
            // Error is handled by NotificationProvider interceptor if it's 422
        } finally {
            setTestingConnection(false);
        }
    };

    const onEdit = (config) => {
        setEditItem(config);
    };

    const onDelete = (config) => {
        handleDelete(config.id, config.name);
    };

    return (
        <>
            <PageLayout
                title="LDAP Configuration"
                description="Manage LDAP directory connections for user authentication and authorization across platforms."
                createConfig={{
                    title: "New LDAP Config",
                    entityPath: "/ldap_configs",
                    buttonText: "NEW CONFIG",
                    initialData: {
                        project_id: selectedProject?.id,
                        verify_ssl: true
                    },
                    onSuccess: handleCreate,
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
                searchQuery={searchTerm}
                onSearchChange={(e) => setSearchTerm(e.target.value)}
                searchPlaceholder="Search LDAP configs..."
                isLoading={loading}
                isEmpty={filteredConfigs.length === 0}
                emptyState={{
                    title: "No LDAP configurations found",
                    description: selectedProject
                        ? `No LDAP configurations found in ${selectedProject.name}.`
                        : 'Create your first LDAP configuration to get started.',
                    icon: <BookA size={48} className="text-slate-700" />
                }}
            >
                <div className="grid grid-cols-1 gap-4">
                    {filteredConfigs.map(config => (
                        <ListingItem
                            key={config.id}
                            icon={BookA}
                            title={config.name}
                            badges={[
                                { text: config.server_url?.startsWith('ldaps') ? 'LDAPS' : 'LDAP', variant: "mw-badge-neutral" },
                            ]}
                            subtitle={config.server_url}
                            onClick={() => onEdit(config)}
                            actions={
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onEdit(config);
                                        }}
                                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                                        title="Edit"
                                    >
                                        <Edit2 className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDelete(config);
                                        }}
                                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                                        title="Delete"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                    <div className="w-px h-8 bg-slate-200 dark:bg-slate-800 mx-2" />
                                    <ChevronRight className="w-5 h-5 text-slate-300 dark:text-slate-600" />
                                </div>
                            }
                        />
                    ))}
                </div >
            </PageLayout >

            {/* Edit Modal */}
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
                            onSuccess={handleUpdate}
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
