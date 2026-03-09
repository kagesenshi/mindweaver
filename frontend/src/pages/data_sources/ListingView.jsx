import React, { useState } from 'react';
import {
    Plus,
    Database,
    Link as LinkIcon,
    RefreshCcw,
    AlertCircle,
    CheckCircle2,
    Globe,
    FileUp,
    Server,
    HardDrive,
    Trash2,
    Edit2,
    ChevronRight,
    Search,
    ExternalLink,
    Library
} from 'lucide-react';
import ListingItem from '../../components/ListingItem';
import { cn } from '../../utils/cn';
import Modal from '../../components/Modal';
import PageLayout from '../../components/PageLayout';
import DynamicForm from '../../components/DynamicForm';

const ListingView = ({ darkMode, dataSourcesHook }) => {
    const { dataSources, loading, deleteDataSource, testConnection, fetchDataSources } = dataSourcesHook;
    const [editSource, setEditSource] = useState(null);
    const [testingId, setTestingId] = useState(null);
    const [testResult, setTestResult] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const filteredDataSources = dataSources.filter(source =>
        (source.title || source.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (source.driver || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleTest = async (id) => {
        setTestingId(id);
        setTestResult(null);
        try {
            const result = await testConnection(id);
            setTestResult({ id, success: true, message: result.message || 'Connection successful' });
        } catch (err) {
            setTestResult({ id, success: false, message: err.response?.data?.detail || 'Connection failed' });
        } finally {
            setTestingId(null);
        }
    };

    const onEdit = (source) => {
        setEditSource(source);
    };

    const onDelete = (source) => {
        deleteDataSource(source.id, source.name);
    };

    const getIcon = (driver) => {
        const d = (driver || '').toLowerCase();
        if (d.includes('s3')) return HardDrive;
        if (d.includes('http') || d.includes('api') || d.includes('web')) return Globe;
        if (d.includes('file') || d.includes('csv')) return FileUp;
        if (d.includes('trino') || d.includes('kafka')) return Server;
        return Database;
    };

    return (
        <>
            <PageLayout
                title="Data Source Registry"
                description="Global connection identities for Trino, Airflow, and ETL runtimes."
                createConfig={{
                    title: "Register Data Source",
                    entityPath: "/data_sources",
                    buttonText: "REGISTER SOURCE",
                    onSuccess: () => {
                        fetchDataSources();
                    }
                }}
                searchQuery={searchTerm}
                onSearchChange={(e) => setSearchTerm(e.target.value)}
                searchPlaceholder="Search data sources..."
                isLoading={loading}
                isEmpty={filteredDataSources.length === 0}
                emptyState={{
                    title: "No data sources found",
                    description: "Register a new data source to use it in your data platform.",
                    icon: <Library size={48} className="text-slate-700" />
                }}
            >
                <div className="grid grid-cols-1 gap-4">
                    {filteredDataSources.map(source => (
                        <div key={source.id}>
                            <ListingItem
                                icon={getIcon(source.driver)}
                                title={source.title || source.name}
                                badges={source.driver ? [{ text: source.driver, variant: "mw-badge-neutral" }] : []}
                                subtitle={
                                    <div className="flex items-center gap-4">
                                        <span>{source.host || 'N/A'}{source.port ? `:${source.port}` : ''}</span>
                                        <span className="text-slate-300 dark:text-slate-600">|</span>
                                        <span>{source.database || source.resource || 'N/A'}</span>
                                    </div>
                                }
                                actions={
                                    <>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onEdit(source);
                                            }}
                                            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                                            title="Edit"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onDelete(source);
                                            }}
                                            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                                            title="Delete"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleTest(source.id);
                                            }}
                                            disabled={testingId === source.id}
                                            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500 disabled:opacity-50"
                                            title={testingId === source.id ? 'TESTING...' : 'Test Connection'}
                                        >
                                            {testingId === source.id ? <RefreshCcw className="w-4 h-4 animate-spin" /> : <LinkIcon className="w-4 h-4" />}
                                        </button>
                                    </>
                                }
                            />
                            {testResult?.id === source.id && (
                                <div className="px-4 pb-4">
                                    <div className={cn(
                                        "p-3 rounded-xl border flex items-center gap-2 text-sm font-bold animate-in fade-in zoom-in-95",
                                        testResult.success
                                            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                                            : "bg-rose-500/10 border-rose-500/20 text-rose-500"
                                    )}>
                                        {testResult.success ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
                                        {testResult.message}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </PageLayout >

            <Modal
                isOpen={!!editSource}
                onClose={() => setEditSource(null)}
                title="Edit Data Source"
                darkMode={darkMode}
            >
                {editSource && (
                    <DynamicForm
                        entityPath="/data_sources"
                        mode="edit"
                        initialData={editSource}
                        darkMode={darkMode}
                        onSuccess={() => {
                            setEditSource(null);
                            fetchDataSources();
                        }}
                        onCancel={() => setEditSource(null)}
                    />
                )}
            </Modal>
        </>
    );
};

export default ListingView;
