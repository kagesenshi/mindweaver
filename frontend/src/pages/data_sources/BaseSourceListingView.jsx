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

const BaseSourceListingView = ({ 
    darkMode, 
    hook, 
    title, 
    description, 
    entityPath, 
    icon: DefaultIcon,
    createTitle = "Register Source",
    createButtonText = "REGISTER SOURCE",
    searchPlaceholder = "Search sources...",
    renderSubtitle
}) => {
    const { items, loading, deleteItem, testConnection, fetchItems } = hook;
    const [editItem, setEditItem] = useState(null);
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

    const renderActions = (item, state, { onDelete }) => (
        <React.Fragment>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    setEditItem(item);
                }}
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                title="Edit"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-edit-2 w-4 h-4"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>
            </button>
            <button
                onClick={(e) => onDelete(e, item)}
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                title="Delete"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-trash-2 w-4 h-4"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
            <button
                onClick={(e) => handleTest(e, item.id)}
                disabled={testingId === item.id}
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500 disabled:opacity-50"
                title={testingId === item.id ? 'TESTING...' : 'Test Connection'}
            >
                {testingId === item.id ? <RefreshCcw className="w-4 h-4 animate-spin" /> : <LinkIcon className="w-4 h-4" />}
            </button>
        </React.Fragment>
    );

    const renderExtraItemContent = (item) => (
        testResult?.id === item.id && (
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
                title={title}
                description={description}
                items={items}
                loading={loading}
                fetchItems={fetchItems}
                deleteItem={deleteItem}
                icon={DefaultIcon}
                entityPath={entityPath}
                createConfig={{
                    title: createTitle,
                    buttonText: createButtonText,
                }}
                searchPlaceholder={searchPlaceholder}
                emptyState={{
                    title: `No ${title.toLowerCase()} found`,
                    description: "Register a new source to use it in your data platform.",
                    icon: <Library size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderIcon={() => DefaultIcon}
                renderActions={renderActions}
                renderExtraItemContent={renderExtraItemContent}
                darkMode={darkMode}
                searchFields={["name", "title"]}
            />

            <Modal
                isOpen={!!editItem}
                onClose={() => setEditItem(null)}
                title={`Edit ${title}`}
                darkMode={darkMode}
            >
                {editItem && (
                    <DynamicForm
                        entityPath={entityPath}
                        mode="edit"
                        initialData={editItem}
                        darkMode={darkMode}
                        onSuccess={() => {
                            setEditItem(null);
                            fetchItems();
                        }}
                        onCancel={() => setEditItem(null)}
                    />
                )}
            </Modal>
        </>
    );
};

export default BaseSourceListingView;
