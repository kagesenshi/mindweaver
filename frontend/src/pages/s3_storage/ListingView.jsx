import React, { useState } from 'react';
import { HardDrive, Radio, CheckCircle2, XCircle } from 'lucide-react';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import GenericListingView from '../../components/GenericListingView';
import { cn } from '../../utils/cn';

const ListingView = ({
    darkMode,
    selectedProject,
    s3Storages,
    onSelectStorage
}) => {
    const { storages, loading, deleteStorage, fetchStorages, testConnection } = s3Storages;

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

    const renderSubtitle = (storage) => (
        <span>{storage.bucket}</span>
    );

    const renderBadges = (storage) => ([
        { text: storage.region, variant: "mw-badge-neutral" }
    ]);

    return (
        <>
            <GenericListingView
                title="S3 Object Storage"
                description="Manage S3-compatible object storage connections for your data platform."
                items={storages}
                loading={loading}
                fetchItems={fetchStorages}
                deleteItem={deleteStorage}
                onSelectItem={(storage) => onSelectStorage(storage)}
                onEditItem={(storage) => setEditItem(storage)}
                icon={HardDrive}
                entityPath="/s3_storages"
                createConfig={{
                    title: "New S3 Storage",
                    buttonText: "NEW STORAGE",
                    initialData: {
                        region: 'us-east-1'
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
                searchPlaceholder="Search storages..."
                emptyState={{
                    title: "No storage buckets found",
                    description: selectedProject
                        ? `No S3 storages configured in ${selectedProject.name}.`
                        : 'Create your first S3 storage connection to get started.',
                    icon: <HardDrive size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderBadges={renderBadges}
                deleteModalConfig={{
                    title: "Delete S3 Storage",
                    message: "Are you sure you want to delete this S3 storage connection? Any projects using it will lose access to the associated bucket."
                }}
                darkMode={darkMode}
                selectedProject={selectedProject}
                searchFields={["name", "title", "region"]}
            />

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
                            onSuccess={() => {
                                fetchStorages();
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
