import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
    HardDrive,
    Plus,
    Radio,
    Globe,
    Shield,
    CheckCircle2,
    XCircle,
    Server
} from 'lucide-react';
import { useS3Storages } from '../hooks/useResources';
import PageLayout from '../components/PageLayout';
import ResourceCard from '../components/ResourceCard';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import { cn } from '../utils/cn';

const S3StoragePage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const {
        storages,
        loading,
        createStorage,
        updateStorage,
        deleteStorage,
        testConnection,
        fetchStorages
    } = useS3Storages();

    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [testResult, setTestResult] = useState(null);
    const [testingConnection, setTestingConnection] = useState(false);

    const filteredStorages = storages.filter(s => {
        const matchesProject = !selectedProject || s.project_id === selectedProject.id;
        const matchesSearch = (s.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (s.region || '').toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && matchesSearch;
    });

    const handleCreate = () => {
        fetchStorages();
        setIsCreateModalOpen(false);
    };

    const handleUpdate = () => {
        fetchStorages();
        setEditItem(null);
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this storage?')) {
            await deleteStorage(id);
        }
    };

    const runTestConnection = async (formData) => {
        setTestingConnection(true);
        setTestResult(null);
        try {
            const result = await testConnection({
                ...formData,
                storage_id: editItem?.id // Pass ID if editing, so backend can decrypt existing secret if redacted
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

    return (
        <>
            <PageLayout
                title="S3 Object Storage"
                description="Manage S3-compatible object storage connections for your data platform."
                headerActions={
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="mw-btn-primary px-4 py-2"
                    >
                        <Plus size={16} /> NEW STORAGE
                    </button>
                }
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
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filteredStorages.map(storage => (
                        <ResourceCard
                            key={storage.id}
                            onClick={() => setEditItem(storage)}
                            icon={<Server size={20} />}
                            title={storage.name}
                            subtitle={storage.region}
                            onEdit={() => setEditItem(storage)}
                            onDelete={() => handleDelete(storage.id)}
                        >
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex items-center gap-2 text-slate-500">
                                    <Globe size={12} />
                                    <span className="text-base font-bold truncate" title={storage.endpoint_url || 'AWS S3'}>
                                        {storage.endpoint_url ? new URL(storage.endpoint_url).hostname : 'AWS Standard'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2 text-blue-500/70">
                                    <Shield size={12} />
                                    <span className="text-base font-bold uppercase truncate">
                                        {storage.access_key ? 'Encrypted' : 'Public'}
                                    </span>
                                </div>
                            </div>
                        </ResourceCard>
                    ))}
                </div>
            </PageLayout>

            {/* Create Modal */}
            <Modal
                isOpen={isCreateModalOpen}
                onClose={() => {
                    setIsCreateModalOpen(false);
                    setTestResult(null);
                }}
                title="New S3 Storage"
                darkMode={darkMode}
            >
                <div className="space-y-4">
                    {testResult && (
                        <div className={cn(
                            "p-4 rounded-xl border flex items-center gap-3 text-sm font-bold",
                            testResult.success
                                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-600"
                                : "bg-rose-500/10 border-rose-500/20 text-rose-600"
                        )}>
                            {testResult.success ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                            {testResult.message}
                        </div>
                    )}
                    <DynamicForm
                        entityPath="/s3_storages"
                        mode="create"
                        darkMode={darkMode}
                        initialData={{
                            project_id: selectedProject?.id,
                            region: 'us-east-1'
                        }}
                        onSuccess={handleCreate}
                        onCancel={() => setIsCreateModalOpen(false)}
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
                </div>
            </Modal>

            {/* Edit Modal */}
            <Modal
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
                        )}>
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
            </Modal>
        </>
    );
};

export default S3StoragePage;
