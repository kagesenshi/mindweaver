import React, { useState, useCallback, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
    HardDrive,
    Plus,
    Radio,
    Globe,

    CheckCircle2,
    XCircle,
    Server,
    Folder,
    File,
    ChevronRight,
    ArrowLeft,
    RotateCcw,
    Upload,
    ChevronUp,
    Search,
    Download,
    Trash2
} from 'lucide-react';
import { useS3Storages } from '../hooks/useResources';
import { useNotification } from '../providers/NotificationProvider';
import PageLayout from '../components/PageLayout';
import ResourceCard from '../components/ResourceCard';
import Modal from '../components/Modal';
import DynamicForm from '../components/DynamicForm';
import ResourceConfirmModal from '../components/ResourceConfirmModal';
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
        fetchStorages,
        browseStorage,
        uploadFile,
        downloadFile,
        deleteFile
    } = useS3Storages();

    const { showSuccess, showError } = useNotification();
    const fileInputRef = useRef(null);
    const [uploading, setUploading] = useState(false);

    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [editItem, setEditItem] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [testResult, setTestResult] = useState(null);
    const [testingConnection, setTestingConnection] = useState(false);

    // Browser State
    const [browsingStorage, setBrowsingStorage] = useState(null);
    const [currentBucket, setCurrentBucket] = useState(null);
    const [currentPrefix, setCurrentPrefix] = useState("");
    const [fsItems, setFsItems] = useState([]);
    const [fsLoading, setFsLoading] = useState(false);
    const [itemToDelete, setItemToDelete] = useState(null);

    const fetchFsItems = useCallback(async (storageId, bucket, prefix) => {
        setFsLoading(true);
        try {
            const data = await browseStorage(storageId, { bucket, prefix });
            setFsItems(data.items || []);
        } catch (err) {
            console.error("Failed to fetch S3 items", err);
        } finally {
            setFsLoading(false);
        }
    }, [browseStorage]);

    const handleBrowse = (storage) => {
        setBrowsingStorage(storage);
        setCurrentBucket(null);
        setCurrentPrefix("");
        fetchFsItems(storage.id);
    };

    const handleSelectBucket = (bucketName) => {
        setCurrentBucket(bucketName);
        setCurrentPrefix("");
        fetchFsItems(browsingStorage.id, bucketName, "");
    };

    const handleSelectDirectory = (path) => {
        setCurrentPrefix(path);
        fetchFsItems(browsingStorage.id, currentBucket, path);
    };

    const handleGoUp = () => {
        if (currentPrefix) {
            const parts = currentPrefix.split('/').filter(Boolean);
            parts.pop();
            const parentPrefix = parts.length > 0 ? parts.join('/') + '/' : "";
            setCurrentPrefix(parentPrefix);
            fetchFsItems(browsingStorage.id, currentBucket, parentPrefix);
        } else if (currentBucket) {
            setCurrentBucket(null);
            fetchFsItems(browsingStorage.id);
        }
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        try {
            await uploadFile(browsingStorage.id, currentBucket, currentPrefix, file);
            showSuccess(`Successfully uploaded ${file.name}`);
            fetchFsItems(browsingStorage.id, currentBucket, currentPrefix);
        } catch (err) {
            console.error("Upload failed", err);
            if (err.response?.status !== 422) {
                showError(err.response?.data?.detail?.msg || err.message || "Upload failed");
            }
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDownload = async (item) => {
        try {
            await downloadFile(browsingStorage.id, currentBucket, item.path);
        } catch (err) {
            console.error("Download failed", err);
            showError(err.response?.data?.detail?.msg || err.message || "Download failed");
        }
    };

    const handleDeleteFile = async (item) => {
        try {
            await deleteFile(browsingStorage.id, currentBucket, item.path);
            showSuccess(`Successfully deleted ${item.name}`);
            fetchFsItems(browsingStorage.id, currentBucket, currentPrefix);
        } catch (err) {
            console.error("Delete failed", err);
            showError(err.response?.data?.detail?.msg || err.message || "Delete failed");
        }
    };

    const filteredStorages = storages.filter(s => {
        const matchesProject = !selectedProject || s.project_id === selectedProject.id;
        const matchesSearch = (s.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (s.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
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

    const handleDelete = async (id, confirmName) => {
        await deleteStorage(id, confirmName);
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

    if (browsingStorage) {
        return (
            <>
                <PageLayout
                    title={browsingStorage.title}
                    description={`Browsing S3 storage: ${browsingStorage.region}`}
                    headerActions={
                        <button
                            onClick={() => setBrowsingStorage(null)}
                            className="mw-btn-secondary px-4 py-2"
                        >
                            <ArrowLeft size={16} /> BACK TO LIST
                        </button>
                    }
                >
                    {/* Browser Navigation Panel */}
                    <div className={cn(
                        "border rounded-2xl p-4 mb-4 flex flex-col md:flex-row md:items-center justify-between gap-4",
                        darkMode ? "bg-slate-900/50 border-slate-700/50" : "bg-white border-slate-200 shadow-sm"
                    )}>
                        <div className="flex items-center gap-2 overflow-hidden">
                            <div className={cn(
                                "flex items-center gap-1 font-bold text-sm shrink-0",
                                darkMode ? "text-slate-400" : "text-slate-500"
                            )}>
                                <Server size={14} />
                                <span>{browsingStorage.name}</span>
                                <ChevronRight size={14} />
                            </div>

                            <div className="flex items-center gap-1 overflow-hidden">
                                <button
                                    onClick={() => {
                                        setCurrentBucket(null);
                                        setCurrentPrefix("");
                                        fetchFsItems(browsingStorage.id);
                                    }}
                                    className={cn(
                                        "px-2 py-1 rounded-md text-sm font-medium transition-colors",
                                        !currentBucket
                                            ? "bg-blue-500/20 text-blue-400"
                                            : cn(darkMode ? "text-slate-400 hover:bg-slate-800" : "text-slate-600 hover:bg-slate-100")
                                    )}
                                >
                                    Root
                                </button>

                                {currentBucket && (
                                    <>
                                        <ChevronRight size={14} className="text-slate-600 shrink-0" />
                                        <button
                                            onClick={() => {
                                                setCurrentPrefix("");
                                                fetchFsItems(browsingStorage.id, currentBucket, "");
                                            }}
                                            className={cn(
                                                "px-2 py-1 rounded-md text-sm font-medium transition-colors shrink-0",
                                                currentBucket && !currentPrefix
                                                    ? "bg-blue-500/20 text-blue-400"
                                                    : cn(darkMode ? "text-slate-400 hover:bg-slate-800" : "text-slate-600 hover:bg-slate-100")
                                            )}
                                        >
                                            {currentBucket}
                                        </button>
                                    </>
                                )}

                                {currentPrefix && currentPrefix.split('/').filter(Boolean).map((part, i, arr) => (
                                    <React.Fragment key={i}>
                                        <ChevronRight size={14} className="text-slate-600 shrink-0" />
                                        <button
                                            onClick={() => {
                                                const prefix = arr.slice(0, i + 1).join('/') + '/';
                                                setCurrentPrefix(prefix);
                                                fetchFsItems(browsingStorage.id, currentBucket, prefix);
                                            }}
                                            className={cn(
                                                "px-2 py-1 rounded-md text-sm font-medium transition-colors shrink-0",
                                                i === arr.length - 1
                                                    ? "bg-blue-500/20 text-blue-400"
                                                    : cn(darkMode ? "text-slate-400 hover:bg-slate-800" : "text-slate-600 hover:bg-slate-100")
                                            )}
                                        >
                                            {part}
                                        </button>
                                    </React.Fragment>
                                ))}
                            </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                            <button
                                disabled={!currentBucket}
                                onClick={handleGoUp}
                                className={cn(
                                    "p-2 rounded-lg border transition-colors",
                                    !currentBucket
                                        ? "bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed opacity-50"
                                        : darkMode
                                            ? "bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 hover:text-white"
                                            : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-blue-600 shadow-sm"
                                )}
                                title={currentBucket ? "Up one level" : "At root level"}
                            >
                                <ChevronUp size={18} />
                            </button>
                            <button
                                disabled={!currentBucket || uploading}
                                onClick={handleUploadClick}
                                className={cn(
                                    "p-2 rounded-lg border transition-colors",
                                    !currentBucket || uploading
                                        ? "bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed opacity-50"
                                        : darkMode
                                            ? "bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 hover:text-white"
                                            : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-blue-600 shadow-sm"
                                )}
                                title={currentBucket ? "Upload File" : "Select a bucket to upload"}
                            >
                                {uploading ? <RotateCcw size={18} className="animate-spin" /> : <Upload size={18} />}
                            </button>
                            <button
                                onClick={() => fetchFsItems(browsingStorage.id, currentBucket, currentPrefix)}
                                className={cn(
                                    "p-2 rounded-lg border transition-colors",
                                    darkMode
                                        ? "bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 hover:text-white"
                                        : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-blue-600 shadow-sm"
                                )}
                                title="Refresh"
                            >
                                <RotateCcw size={18} />
                            </button>
                        </div>
                    </div>

                    {/* Main Content Areas */}
                    <div className={cn(
                        "border rounded-2xl overflow-hidden",
                        darkMode ? "bg-slate-900/30 border-slate-800/50" : "bg-white border-slate-200 shadow-sm"
                    )}>
                        <div className={cn(
                            "px-6 py-4 border-b flex items-center justify-between",
                            darkMode ? "border-slate-800 bg-slate-900/50" : "border-slate-100 bg-slate-50/50"
                        )}>
                            <h3 className={cn(
                                "text-sm font-bold uppercase tracking-wider",
                                darkMode ? "text-slate-400" : "text-slate-500"
                            )}>
                                {currentBucket ? `Contents of ${currentBucket}/${currentPrefix}` : 'Available Buckets'}
                            </h3>
                            <div className="flex items-center gap-2 text-xs text-slate-500">
                                <Search size={12} />
                                <span>{fsItems.length} items</span>
                            </div>
                        </div>

                        <div className={cn(
                            "divide-y",
                            darkMode ? "divide-slate-800/50" : "divide-slate-100"
                        )}>
                            {fsLoading ? (
                                <div className="p-12 flex flex-col items-center justify-center gap-4 text-slate-500">
                                    <RotateCcw size={32} className="animate-spin text-blue-500" />
                                    <span className="font-bold">Fetching S3 data...</span>
                                </div>
                            ) : fsItems.length === 0 ? (
                                <div className="p-12 flex flex-col items-center justify-center gap-4 text-slate-600">
                                    <Search size={48} opacity={0.2} />
                                    <span className="text-lg font-bold">No items found</span>
                                    <p className="text-sm">This {currentBucket ? 'folder' : 'storage'} is empty.</p>
                                </div>
                            ) : (
                                fsItems.map((item, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => {
                                            if (item.type === 'directory') handleSelectDirectory(item.path);
                                            else if (!currentBucket) handleSelectBucket(item.name);
                                        }}
                                        className={cn(
                                            "px-6 py-4 flex items-center justify-between transition-colors cursor-pointer group",
                                            darkMode ? "hover:bg-slate-800/30" : "hover:bg-slate-50",
                                            item.type === 'file' && "cursor-default hover:bg-transparent"
                                        )}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={cn(
                                                "w-10 h-10 rounded-xl flex items-center justify-center border transition-all duration-300",
                                                !currentBucket ? (
                                                    darkMode
                                                        ? "bg-orange-500/10 border-orange-500/20 text-orange-500 group-hover:scale-110 group-hover:bg-orange-500/20"
                                                        : "bg-orange-50 border-orange-100 text-orange-600 group-hover:scale-110 group-hover:bg-orange-100"
                                                ) : item.type === 'directory' ? (
                                                    darkMode
                                                        ? "bg-amber-500/10 border-amber-500/20 text-amber-500 group-hover:scale-110 group-hover:bg-amber-500/20"
                                                        : "bg-amber-50 border-amber-100 text-amber-600 group-hover:scale-110 group-hover:bg-amber-100"
                                                ) : (
                                                    darkMode
                                                        ? "bg-blue-500/10 border-blue-500/20 text-blue-500"
                                                        : "bg-blue-50 border-blue-100 text-blue-600"
                                                )
                                            )}>
                                                {!currentBucket ? <HardDrive size={20} /> :
                                                    item.type === 'directory' ? <Folder size={20} /> :
                                                        <File size={20} />}
                                            </div>
                                            <div>
                                                <div className={cn(
                                                    "font-medium transition-colors text-base",
                                                    darkMode ? "text-slate-200 group-hover:text-white" : "text-slate-900 group-hover:text-blue-600"
                                                )}>
                                                    {item.name}
                                                </div>
                                                <div className="text-xs text-slate-500 font-medium">
                                                    {!currentBucket ? `Created ${new Date(item.creation_date).toLocaleDateString()}` :
                                                        item.type === 'directory' ? 'Folder' :
                                                            `${(item.size / 1024 / 1024).toFixed(2)} MB • Updated ${new Date(item.last_modified).toLocaleString()}`}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            {item.type === 'file' && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDownload(item);
                                                    }}
                                                    className={cn(
                                                        "p-2 rounded-lg border transition-colors opacity-0 group-hover:opacity-100",
                                                        darkMode
                                                            ? "bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 hover:text-white"
                                                            : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-blue-600 shadow-sm"
                                                    )}
                                                    title="Download"
                                                >
                                                    <Download size={16} />
                                                </button>
                                            )}

                                            {item.type === 'file' && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setItemToDelete(item);
                                                    }}
                                                    className={cn(
                                                        "p-2 rounded-lg border transition-colors opacity-0 group-hover:opacity-100",
                                                        darkMode
                                                            ? "bg-slate-800 text-slate-200 border-slate-700 hover:bg-rose-500/20 hover:text-rose-500"
                                                            : "bg-white text-slate-600 border-slate-200 hover:bg-rose-50 hover:text-rose-600 shadow-sm"
                                                    )}
                                                    title="Delete"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            )}

                                            {(item.type === 'directory' || !currentBucket) && (
                                                <ChevronRight size={18} className={cn(
                                                    "transition-all",
                                                    darkMode ? "text-slate-600 group-hover:text-slate-400 group-hover:translate-x-1" : "text-slate-300 group-hover:text-slate-500 group-hover:translate-x-1"
                                                )} />
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </PageLayout>
                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    onChange={handleFileChange}
                />

                {/* File Delete Confirmation */}
                <ResourceConfirmModal
                    isOpen={!!itemToDelete}
                    onClose={() => setItemToDelete(null)}
                    onConfirm={() => handleDeleteFile(itemToDelete)}
                    resourceName={itemToDelete?.name || ''}
                    darkMode={darkMode}
                    title="Delete File"
                    message="Are you sure you want to delete this file? This action is permanent."
                    confirmText="DELETE FILE"
                    variant="danger"
                    icon={Trash2}
                />
            </>
        );
    }

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
                            onClick={() => handleBrowse(storage)}
                            icon={<Server size={20} />}
                            title={storage.title}
                            subtitle={storage.region}
                            onEdit={() => setEditItem(storage)}
                            resourceName={storage.name}
                            darkMode={darkMode}
                            onDelete={(name) => handleDelete(storage.id, name)}
                        >
                            <div className="flex items-center gap-2 text-slate-500">
                                <Globe size={12} />
                                <span className="text-base font-bold truncate" title={storage.endpoint_url || 'AWS S3'}>
                                    {storage.endpoint_url ? new URL(storage.endpoint_url).hostname : 'AWS Standard'}
                                </span>
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

            <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                onChange={handleFileChange}
            />
        </>
    );
};

export default S3StoragePage;
