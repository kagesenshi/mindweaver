import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
    Plus,
    Library,
    Database,
    Trash2,
    Key,
    Link as LinkIcon,
    RefreshCcw,
    AlertCircle,
    CheckCircle2,
    Save,
    X,
    Globe,
    FileUp,
    Edit2
} from 'lucide-react';
import { useDataSources, useProjects } from '../hooks/useResources';
import { cn } from '../utils/cn';
import ResourceCard from '../components/ResourceCard';
import Modal from '../components/Modal';
import PageLayout from '../components/PageLayout';

const DataSourceForm = ({ mode = 'create', initialData = {}, onSuccess, onCancel, darkMode }) => {
    const { projects } = useProjects();
    const { createDataSource, updateDataSource, testConnection } = useDataSources();
    const [formData, setFormData] = useState({
        name: '',
        title: '',
        type: 'API',
        project_id: '',
        parameters: {},
        ...initialData
    });
    const [fieldErrors, setFieldErrors] = useState({});
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState(null);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (mode === 'edit' && initialData) {
            setFormData({ ...initialData });
        }
    }, [mode, initialData]);

    const handleChange = (path, value) => {
        // Clear field error on change
        setFieldErrors(prev => {
            const next = { ...prev };
            delete next[path];
            return next;
        });

        const keys = path.split('.');
        if (keys.length > 1) {
            setFormData(prev => ({
                ...prev,
                [keys[0]]: {
                    ...prev[keys[0]],
                    [keys[1]]: value
                }
            }));
        } else {
            if (path === 'type' && mode === 'create') {
                const defaults = {
                    API: { base_url: '', api_key: '' },
                    Database: { host: '', port: 5432, username: '', password: '', database: '', database_type: 'postgresql' },
                    'Web Scraper': { start_url: '' },
                    'File Upload': {}
                };
                setFormData(prev => ({
                    ...prev,
                    type: value,
                    parameters: defaults[value] || {}
                }));
            } else {
                setFormData(prev => ({ ...prev, [path]: value }));
            }
        }
    };

    const handleTest = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            // In a real scenario, we might need to send the full data or just the ID if it exists
            // Flutter implementation sends the type and parameters
            const result = await testConnection(formData.id); // Assuming backend expects ID for existing
            // If it's a new one, we might need a different endpoint or handle it differently
            // but the current hook only supports testConnection(id)
            setTestResult({ success: true, message: result.message || 'Connection successful' });
        } catch (err) {
            setTestResult({ success: false, message: err.response?.data?.detail || 'Connection failed' });
        } finally {
            setTesting(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        setFieldErrors({});
        try {
            if (mode === 'create') {
                await createDataSource(formData);
            } else {
                await updateDataSource(formData.id, formData);
            }
            onSuccess();
        } catch (err) {
            const detail = err.response?.data?.detail;
            if (detail) {
                const errors = {};
                const details = Array.isArray(detail) ? detail : [detail];

                details.forEach(err => {
                    if (err.loc && Array.isArray(err.loc)) {
                        let pathParts = err.loc;
                        // Skip common prefixes from FastAPI/Pydantic
                        if (['body', 'query', 'header'].includes(pathParts[0])) {
                            pathParts = pathParts.slice(1);
                        }
                        const path = pathParts.join('.');
                        errors[path] = err.msg;
                    }
                });

                if (Object.keys(errors).length > 0) {
                    setFieldErrors(errors);
                    setError('Please fix the errors below.');
                } else {
                    setError(err.response?.data?.detail?.msg || err.message || 'Operation failed');
                }
            } else {
                setError(err.message || 'Operation failed');
            }
        } finally {
            setSaving(false);
        }
    };


    const FieldError = ({ name }) => {
        if (!fieldErrors[name]) return null;
        return <p className="text-sm text-rose-500 mt-1 font-medium">{fieldErrors[name]}</p>;
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3 text-rose-500 text-base">
                    <AlertCircle size={18} />
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                    <label className={cn("mw-label", fieldErrors.project_id ? "text-rose-500" : "")}>Project</label>
                    <select
                        value={formData.project_id || ''}
                        onChange={(e) => handleChange('project_id', parseInt(e.target.value))}
                        className={cn("mw-input", fieldErrors.project_id && "border-rose-500 ring-1 ring-rose-500/50")}
                    >
                        <option value="">Select Project...</option>
                        {projects.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
                    </select>
                    <FieldError name="project_id" />
                </div>
                <div className="space-y-2">
                    <label className={cn("mw-label", fieldErrors.type ? "text-rose-500" : "")}>Source Type</label>
                    <select
                        value={formData.type}
                        onChange={(e) => handleChange('type', e.target.value)}
                        className={cn("mw-input", fieldErrors.type && "border-rose-500 ring-1 ring-rose-500/50")}
                        disabled={mode === 'edit'}
                    >
                        <option value="API">REST API</option>
                        <option value="Database">Database</option>
                        <option value="Web Scraper">Web Scraper</option>
                        <option value="File Upload">File Upload</option>
                    </select>
                    <FieldError name="type" />
                </div>
                <div className="space-y-2">
                    <label className={cn("mw-label", fieldErrors.name ? "text-rose-500" : "")}>Name (ID)</label>
                    <input
                        value={formData.name}
                        onChange={(e) => handleChange('name', e.target.value)}
                        className={cn("mw-input font-mono", fieldErrors.name && "border-rose-500 ring-1 ring-rose-500/50")}
                        disabled={mode === 'edit'}
                    />
                    <FieldError name="name" />
                </div>
                <div className="space-y-2">
                    <label className={cn("mw-label", fieldErrors.title ? "text-rose-500" : "")}>Title</label>
                    <input
                        value={formData.title}
                        onChange={(e) => handleChange('title', e.target.value)}
                        className={cn("mw-input", fieldErrors.title && "border-rose-500 ring-1 ring-rose-500/50")}
                    />
                    <FieldError name="title" />
                </div>
            </div>

            <div className="pt-4 border-t border-slate-800/50">
                <h4 className="text-base font-bold text-slate-400 uppercase tracking-[0.2em] mb-4">Configuration</h4>

                {formData.type === 'API' && (
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className={cn("mw-label", fieldErrors['parameters.base_url'] ? "text-rose-500" : "")}>Base URL</label>
                            <input
                                value={formData.parameters.base_url || ''}
                                onChange={(e) => handleChange('parameters.base_url', e.target.value)}
                                className={cn("mw-input", fieldErrors['parameters.base_url'] && "border-rose-500 ring-1 ring-rose-500/50")}
                                placeholder="https://api.example.com"
                            />
                            <FieldError name="parameters.base_url" />
                        </div>
                        <div className="space-y-2">
                            <label className={cn("mw-label", fieldErrors['parameters.api_key'] ? "text-rose-500" : "")}>API Key</label>
                            <input
                                type="password"
                                value={formData.parameters.api_key === '__REDACTED__' ? '__REDACTED__' : (formData.parameters.api_key || '')}
                                onChange={(e) => handleChange('parameters.api_key', e.target.value)}
                                className={cn("mw-input", fieldErrors['parameters.api_key'] && "border-rose-500 ring-1 ring-rose-500/50")}
                            />
                            <FieldError name="parameters.api_key" />
                        </div>
                    </div>
                )}

                {formData.type === 'Database' && (
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className={cn("mw-label", fieldErrors['parameters.database_type'] ? "text-rose-500" : "")}>DB Type</label>
                                <select
                                    value={formData.parameters.database_type || ''}
                                    onChange={(e) => handleChange('parameters.database_type', e.target.value)}
                                    className={cn("mw-input", fieldErrors['parameters.database_type'] && "border-rose-500 ring-1 ring-rose-500/50")}
                                >
                                    <option value="postgresql">PostgreSQL</option>
                                    <option value="mysql">MySQL</option>
                                </select>
                                <FieldError name="parameters.database_type" />
                            </div>
                            <div className="space-y-2">
                                <label className={cn("mw-label", fieldErrors['parameters.host'] ? "text-rose-500" : "")}>Host</label>
                                <input
                                    value={formData.parameters.host || ''}
                                    onChange={(e) => handleChange('parameters.host', e.target.value)}
                                    className={cn("mw-input", fieldErrors['parameters.host'] && "border-rose-500 ring-1 ring-rose-500/50")}
                                />
                                <FieldError name="parameters.host" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className={cn("mw-label", fieldErrors['parameters.port'] ? "text-rose-500" : "")}>Port</label>
                                <input
                                    type="number"
                                    value={formData.parameters.port ?? ''}
                                    onChange={(e) => handleChange('parameters.port', e.target.value === '' ? undefined : parseInt(e.target.value))}
                                    className={cn("mw-input", fieldErrors['parameters.port'] && "border-rose-500 ring-1 ring-rose-500/50")}
                                />
                                <FieldError name="parameters.port" />
                            </div>
                            <div className="space-y-2">
                                <label className={cn("mw-label", fieldErrors['parameters.username'] ? "text-rose-500" : "")}>Username</label>
                                <input
                                    value={formData.parameters.username || ''}
                                    onChange={(e) => handleChange('parameters.username', e.target.value)}
                                    className={cn("mw-input", fieldErrors['parameters.username'] && "border-rose-500 ring-1 ring-rose-500/50")}
                                />
                                <FieldError name="parameters.username" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className={cn("mw-label", fieldErrors['parameters.password'] ? "text-rose-500" : "")}>Password</label>
                                <input
                                    type="password"
                                    value={formData.parameters.password === '__REDACTED__' ? '__REDACTED__' : (formData.parameters.password || '')}
                                    onChange={(e) => handleChange('parameters.password', e.target.value)}
                                    className={cn("mw-input", fieldErrors['parameters.password'] && "border-rose-500 ring-1 ring-rose-500/50")}
                                />
                                <FieldError name="parameters.password" />
                            </div>
                            <div className="space-y-2">
                                <label className={cn("mw-label", fieldErrors['parameters.database'] ? "text-rose-500" : "")}>Database Name</label>
                                <input
                                    value={formData.parameters.database || ''}
                                    onChange={(e) => handleChange('parameters.database', e.target.value)}
                                    className={cn("mw-input", fieldErrors['parameters.database'] && "border-rose-500 ring-1 ring-rose-500/50")}
                                />
                                <FieldError name="parameters.database" />
                            </div>
                        </div>
                    </div>
                )}

                {formData.type === 'Web Scraper' && (
                    <div className="space-y-2">
                        <label className={cn("mw-label", fieldErrors['parameters.start_url'] ? "text-rose-500" : "")}>Start URL</label>
                        <input
                            value={formData.parameters.start_url || ''}
                            onChange={(e) => handleChange('parameters.start_url', e.target.value)}
                            className={cn("mw-input", fieldErrors['parameters.start_url'] && "border-rose-500 ring-1 ring-rose-500/50")}
                        />
                        <FieldError name="parameters.start_url" />
                    </div>
                )}

                {formData.type === 'File Upload' && (
                    <div className="p-8 border-2 border-dashed border-slate-800 rounded-2xl text-center">
                        <FileUp size={32} className="mx-auto text-slate-600 mb-2" />
                        <p className="text-sm text-slate-500">File upload configuration will appear here.</p>
                    </div>
                )}
            </div>

            {testResult && (
                <div className={cn(
                    "p-3 rounded-xl border flex items-center gap-2 text-base font-medium animate-in fade-in zoom-in-95",
                    testResult.success
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500"
                        : "bg-rose-500/10 border-rose-500/20 text-rose-500"
                )}>
                    {testResult.success ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                    {testResult.message}
                </div>
            )}

            <div className="flex items-center gap-4 pt-4">
                {mode === 'edit' && (
                    <button
                        type="button"
                        onClick={handleTest}
                        disabled={testing}
                        className="mw-btn-secondary flex-1 py-4"
                    >
                        {testing ? <RefreshCcw size={18} className="animate-spin" /> : <LinkIcon size={18} />}
                        {testing ? 'TESTING...' : 'TEST CONNECTION'}
                    </button>
                )}
                <button
                    type="submit"
                    disabled={saving}
                    className="mw-btn-primary flex-1 py-4"
                >
                    {saving ? <RefreshCcw size={18} className="animate-spin" /> : <Save size={18} />}
                    {saving ? 'SAVING...' : (mode === 'create' ? 'REGISTER SOURCE' : 'SAVE CHANGES')}
                </button>
                <button
                    type="button"
                    onClick={onCancel}
                    className="mw-btn-secondary px-8 py-4"
                >
                    <X size={18} /> CANCEL
                </button>
            </div>
        </form>
    );
};

const DataSourcesPage = () => {
    const { darkMode } = useOutletContext();
    const { dataSources, loading, deleteDataSource, testConnection, fetchDataSources } = useDataSources();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [editSource, setEditSource] = useState(null);
    const [testingId, setTestingId] = useState(null);
    const [testResult, setTestResult] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const filteredDataSources = dataSources.filter(source =>
        (source.title || source.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (source.type || '').toLowerCase().includes(searchTerm.toLowerCase())
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


    const getIcon = (type) => {
        switch (type) {
            case 'Database': return <Database size={24} />;
            case 'Web Scraper': return <Globe size={24} />;
            case 'File Upload': return <FileUp size={24} />;
            default: return <Database size={24} />;
        }
    };

    return (
        <PageLayout
            title="Data Source Registry"
            description="Global connection identities for Trino, Airflow, and ETL runtimes."
            headerActions={
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="mw-btn-primary px-4 py-2"
                >
                    <Plus size={16} /> REGISTER SOURCE
                </button>
            }
            searchQuery={searchTerm}
            onSearchChange={(e) => setSearchTerm(e.target.value)}
            searchPlaceholder="Search data sources..."
        >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {loading ? (
                    <div className="col-span-full py-20 flex flex-col items-center justify-center space-y-4">
                        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                        <p className="text-slate-500 text-base font-medium">Fetching data sources...</p>
                    </div>
                ) : filteredDataSources.length === 0 ? (
                    <div className="col-span-full py-20 text-center border-2 border-dashed border-slate-800 rounded-[40px]">
                        <Library size={48} className="mx-auto text-slate-700 mb-4" />
                        <h3 className="text-lg font-bold text-slate-400">No data sources found</h3>
                        <p className="text-slate-500 text-sm">Register a new data source to use it in your data platform.</p>
                    </div> // Using closing brace from original code won't match if I replaced start of return. I need to be careful.
                ) : filteredDataSources.map(source => (
                    <ResourceCard
                        key={source.id}
                        icon={getIcon(source.type)}
                        title={source.title || source.name}
                        subtitle={`${source.id} • ${source.type}`}
                        status={source.status || 'connected'}
                        onEdit={() => setEditSource(source)}
                        onDelete={() => deleteDataSource(source.id)}
                        footer={
                            <button
                                onClick={() => handleTest(source.id)}
                                disabled={testingId === source.id}
                                className="text-sm font-bold text-blue-500 hover:text-blue-400 uppercase tracking-widest flex items-center gap-1.5 transition-colors disabled:opacity-50"
                            >
                                {testingId === source.id ? <RefreshCcw size={12} className="animate-spin" /> : <LinkIcon size={12} />}
                                {testingId === source.id ? 'Testing...' : 'Test Connection'}
                            </button>
                        }
                    >
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <p className="text-sm text-slate-500 font-bold uppercase mb-1">Type</p>
                                <p className={cn("text-sm font-medium", darkMode ? 'text-slate-300' : 'text-slate-700')}>
                                    {source.type}
                                </p>
                            </div>
                            <div>
                                <p className="text-sm text-slate-500 font-bold uppercase mb-1">Configuration</p>
                                <p className={cn("text-sm font-mono truncate", darkMode ? 'text-slate-300' : 'text-slate-700')}>
                                    {source.parameters?.host || source.parameters?.account || source.parameters?.bucket || source.parameters?.base_url || 'Cloud Native'}
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

            <Modal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                title="Register Data Source"
                darkMode={darkMode}
            >
                <DataSourceForm
                    mode="create"
                    darkMode={darkMode}
                    onSuccess={() => {
                        setIsCreateModalOpen(false);
                        fetchDataSources();
                    }}
                    onCancel={() => setIsCreateModalOpen(false)}
                />
            </Modal>

            <Modal
                isOpen={!!editSource}
                onClose={() => setEditSource(null)}
                title="Edit Data Source"
                darkMode={darkMode}
            >
                {editSource && (
                    <DataSourceForm
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
        </PageLayout>
    );
};

export default DataSourcesPage;
