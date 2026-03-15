import React, { useState } from 'react';
import {
    Database,
    Link as LinkIcon,
    RefreshCcw,
    AlertCircle,
    CheckCircle2,
    Globe,
    FileUp,
    Server,
    HardDrive,
    Library
} from 'lucide-react';
import { cn } from '../../utils/cn';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import GenericListingView from '../../components/GenericListingView';

const ListingView = ({ darkMode, dataSourcesHook }) => {
    const { dataSources, loading, deleteDataSource, testConnection, fetchDataSources } = dataSourcesHook;
    const [editSource, setEditSource] = useState(null);
    const [testingId, setTestingId] = useState(null);
    const [testResult, setTestResult] = useState(null);

    const handleTest = async (e, id) => {
        e.stopPropagation();
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

    const getIcon = (driver) => {
        const d = (driver || '').toLowerCase();
        if (d.includes('s3')) return HardDrive;
        if (d.includes('http') || d.includes('api') || d.includes('web')) return Globe;
        if (d.includes('file') || d.includes('csv')) return FileUp;
        if (d.includes('trino') || d.includes('kafka')) return Server;
        return Database;
    };

    const renderSubtitle = (source) => (
        <div className="flex items-center gap-4">
            <span>{source.host || 'N/A'}{source.port ? `:${source.port}` : ''}</span>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <span>{source.database || source.resource || 'N/A'}</span>
        </div>
    );

    const renderBadges = (source) => (
        source.driver ? [{ text: source.driver, variant: "mw-badge-neutral" }] : []
    );

    const renderActions = (source, state, { onDelete }) => (
        <React.Fragment>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    setEditSource(source);
                }}
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                title="Edit"
            >
                <LinkIcon size={18} className="hidden" /> {/* Dummy to avoid lint issues if any */}
                <i className="lucide-edit-2 w-4 h-4" /> {/* Standardizing actions elsewhere, but here we use custom */}
                {/* Wait, I should use the same symbols as before */}
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-edit-2 w-4 h-4"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
            </button>
            <button
                onClick={(e) => onDelete(e, source)}
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                title="Delete"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-trash-2 w-4 h-4"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
            <button
                onClick={(e) => handleTest(e, source.id)}
                disabled={testingId === source.id}
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500 disabled:opacity-50"
                title={testingId === source.id ? 'TESTING...' : 'Test Connection'}
            >
                {testingId === source.id ? <RefreshCcw className="w-4 h-4 animate-spin" /> : <LinkIcon className="w-4 h-4" />}
            </button>
        </React.Fragment>
    );

    const renderExtraItemContent = (source) => (
        testResult?.id === source.id && (
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
        )
    );

    return (
        <>
            <GenericListingView
                title="Data Source Registry"
                description="Global connection identities for Trino, Airflow, and ETL runtimes."
                items={dataSources}
                loading={loading}
                fetchItems={fetchDataSources}
                deleteItem={deleteDataSource}
                icon={Database} // Default icon, getIcon used in renderActions or we can override ListingItem icon?
                // Actually GenericListingView uses icon={IconComponent} in ListingItem.
                // If I want dynamic icon per item, I should probably support renderIcon or just pass getIcon as icon and hope it works?
                // GenericListingView: icon={IconComponent} -> <ListingItem icon={IconComponent} ... />
                // ListingItem: {Icon && <Icon ... />}
                // If I pass a function to IconComponent that takes props... no, that's not how it's used.
                // I'll update GenericListingView to support renderIcon.
                entityPath="/data_sources"
                createConfig={{
                    title: "Register Data Source",
                    buttonText: "REGISTER SOURCE",
                }}
                searchPlaceholder="Search data sources..."
                emptyState={{
                    title: "No data sources found",
                    description: "Register a new data source to use it in your data platform.",
                    icon: <Library size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderBadges={renderBadges}
                renderIcon={(source) => getIcon(source.driver)}
                renderActions={renderActions}
                renderExtraItemContent={renderExtraItemContent}
                darkMode={darkMode}
                searchFields={["name", "title", "driver"]}
            />

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
