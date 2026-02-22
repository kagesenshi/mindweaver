import React, { useState } from 'react';
import {
    Library,
    Database,
    Link as LinkIcon,
    RefreshCcw,
    AlertCircle,
    CheckCircle2,
    Globe,
    FileUp,
    Server,
    HardDrive
} from 'lucide-react';
import { cn } from '../../utils/cn';
import ResourceCard from '../../components/ResourceCard';
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

    const getIcon = (driver) => {
        const d = (driver || '').toLowerCase();
        if (d.includes('postgres') || d.includes('mysql') || d.includes('mongo') || d.includes('sql')) return <Database size={24} />;
        if (d.includes('web') || d.includes('http') || d.includes('api')) return <Globe size={24} />;
        if (d.includes('file') || d.includes('upload') || d.includes('csv')) return <FileUp size={24} />;
        if (d.includes('trino')) return <Server size={24} />;
        return <HardDrive size={24} />;
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredDataSources.map(source => (
                        <ResourceCard
                            key={source.id}
                            icon={getIcon(source.driver)}
                            title={source.title || source.name}
                            subtitle={`${source.id} • ${source.driver}`}
                            status={source.status}
                            onEdit={() => setEditSource(source)}
                            resourceName={source.name}
                            darkMode={darkMode}
                            onDelete={(name) => deleteDataSource(source.id, name)}
                            footer={
                                <button
                                    onClick={() => handleTest(source.id)}
                                    disabled={testingId === source.id}
                                    className="text-base font-bold text-blue-500 hover:text-blue-400 uppercase tracking-widest flex items-center gap-1.5 transition-colors disabled:opacity-50"
                                >
                                    {testingId === source.id ? <RefreshCcw size={12} className="animate-spin" /> : <LinkIcon size={12} />}
                                    {testingId === source.id ? 'Testing...' : 'Test Connection'}
                                </button>
                            }
                        >
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-base text-slate-500 font-bold uppercase mb-1">Driver</p>
                                    <p className={cn("text-base font-medium", darkMode ? 'text-slate-300' : 'text-slate-700')}>
                                        {source.driver}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-base text-slate-500 font-bold uppercase mb-1">Host/Resource</p>
                                    <p className={cn("text-base font-mono truncate", darkMode ? 'text-slate-300' : 'text-slate-700')}>
                                        {source.host || source.resource || 'N/A'}
                                    </p>
                                </div>
                            </div>

                            {testResult?.id === source.id && (
                                <div className={cn(
                                    "mb-4 p-3 rounded-xl border flex items-center gap-2 text-base font-medium animate-in fade-in zoom-in-95",
                                    testResult.success
                                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                                        : "bg-rose-500/10 border-rose-500/20 text-rose-500"
                                )}>
                                    {testResult.success ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                                    {testResult.message}
                                </div>
                            )}
                        </ResourceCard>
                    ))}
                </div>
            </PageLayout>

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
