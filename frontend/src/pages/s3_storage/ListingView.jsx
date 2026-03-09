import React, { useState } from 'react';
import { Plus, Shield, Key, Search, RefreshCw, Trash2, Edit2, ExternalLink, HardDrive, Radio, CheckCircle2, XCircle, ChevronRight } from 'lucide-react';
import ListingItem from '../../components/ListingItem';
import PageLayout from '../../components/PageLayout';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import { cn } from '../../utils/cn';

const ListingView = ({
    darkMode,
    selectedProject,
    s3Storages,
    onSelectStorage
}) => {
    const { storages, loading, deleteStorage, fetchStorages, testConnection } = s3Storages;

    const [searchTerm, setSearchTerm] = useState('');
    const [editItem, setEditItem] = useState(null);
    const [testResult, setTestResult] = useState(null);
    const [testingConnection, setTestingConnection] = useState(false);

    const filteredStorages = storages.filter(s => {
        const matchesProject = !selectedProject || s.project_id === selectedProject.id;
        const matchesSearch = (s.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (s.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (s.region || '').toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && matchesSearch;
    });

    const handleCreate = () => {
        fetchStorages();
    };

    const handleUpdate = () => {
        fetchStorages();
        setEditItem(null);
    };

    const handleDelete = async (id, confirmName) => {
        await deleteStorage(id, confirmName);
    };

    const runTestConnection = async (formData) => {
        setTestingConnection(true);
        setTestResult(null);
        try {
            const result = await testConnection({
                ...formData,
                storage_id: editItem?.id
            });
            setTestResult({
                success: true,
                message: result.message || 'Connection successful!'
            });
        } catch (err) {
            setTestResult({
                success: false,
                message: err.response?.data?.detail?.msg || err.message || 'Connection failed'
            });
        } finally {
            setTestingConnection(false);
        }
    };

    const onEdit = (storage) => {
        setEditItem(storage);
    };

    const onDelete = (storage) => {
        handleDelete(storage.id, storage.name);
    };

    return (
        <>
            <PageLayout
                title="S3 Object Storage"
                description="Manage S3-compatible object storage connections for your data platform."
                createConfig={{
                    title: "New S3 Storage",
                    entityPath: "/s3_storages",
                    buttonText: "NEW STORAGE",
                    initialData: {
                        project_id: selectedProject?.id,
                        region: 'us-east-1'
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
                searchPlaceholder="Search storages..."
                isLoading={loading}
                isEmpty={filteredStorages.length === 0}
                emptyState={{
                    title: "No storage buckets found",
                    description: selectedProject
                        ? `No S3 storages configured in ${selectedProject.name}.`
                        : 'Create your first S3 storage connection to get started.',
                    icon: <HardDrive size={48} className="text-slate-700" />
                }}
            >
                <div className="grid grid-cols-1 gap-4">
                    {filteredStorages.map(storage => (
                        <ListingItem
                            key={storage.id}
                            icon={HardDrive}
                            title={storage.name}
                            badges={[{ text: storage.region, variant: "mw-badge-neutral" }]}
                            subtitle={storage.bucket}
                            onClick={() => onSelectStorage(storage)}
                            actions={
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onEdit(storage);
                                        }}
                                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                                        title="Edit"
                                    >
                                        <Edit2 className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDelete(storage);
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
            < Modal
                isOpen={!!editItem}
                onClose={() => {
                    setEditItem(null);
                    setTestResult(null);
                }}
                title="Edit S3 Storage"
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
                            entityPath="/s3_storages"
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
