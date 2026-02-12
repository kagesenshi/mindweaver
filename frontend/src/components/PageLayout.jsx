import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Search, Loader2, Plus } from 'lucide-react';
import { cn } from '../utils/cn';
import Modal from './Modal';
import DynamicForm from './DynamicForm';

const PageLayout = ({
    title,
    description,
    headerActions,
    createConfig, // { title, entityPath, buttonText, icon, initialData, onSuccess, renderExtraActions, extraContent }
    searchQuery,
    onSearchChange,
    searchPlaceholder = "Search...",
    children,
    isLoading = false,
    isEmpty = false,
    emptyState = null,
    className
}) => {
    const { darkMode } = useOutletContext() || {};
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    const CreateIcon = createConfig?.icon || Plus;

    return (
        <div className={cn("space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300", className)}>
            <div className="mw-page-header">
                <div>
                    <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">
                        {title}
                    </h2>
                    {description && (
                        <p className="text-slate-500 mt-1 text-base">
                            {description}
                        </p>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {createConfig && (
                        <button
                            onClick={() => setIsCreateModalOpen(true)}
                            className="mw-btn-primary px-4 py-2"
                        >
                            <CreateIcon size={16} /> {createConfig.buttonText || 'CREATE'}
                        </button>
                    )}
                    {headerActions}
                </div>
            </div>

            {onSearchChange && (
                <div className="flex items-center gap-4 mb-8">
                    <div className="mw-search-box flex-1">
                        <Search size={18} className="text-slate-500" />
                        <input
                            type="text"
                            placeholder={searchPlaceholder}
                            className="bg-transparent text-base focus:outline-none w-full"
                            value={searchQuery || ''}
                            onChange={onSearchChange}
                        />
                    </div>
                </div>
            )}

            {isLoading ? (
                <div className="col-span-full py-20 flex flex-col items-center justify-center space-y-4">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-slate-500 text-base font-medium">Loading...</p>
                </div>
            ) : isEmpty ? (
                <PageLayout.EmptyState
                    icon={emptyState?.icon}
                    title={emptyState?.title || "No items found"}
                    description={emptyState?.description || "There are no items to display."}
                    className={emptyState?.className}
                >
                    {React.isValidElement(emptyState) ? emptyState : emptyState?.children}
                </PageLayout.EmptyState>
            ) : (
                children
            )}

            {createConfig && (
                <Modal
                    isOpen={isCreateModalOpen}
                    onClose={() => {
                        setIsCreateModalOpen(false);
                        if (createConfig.onClose) {
                            createConfig.onClose();
                        }
                    }}
                    title={createConfig.title || `Create ${title}`}
                    darkMode={darkMode}
                >
                    <div className="space-y-4">
                        {createConfig.extraContent}
                        <DynamicForm
                            entityPath={createConfig.entityPath}
                            mode="create"
                            initialData={createConfig.initialData}
                            darkMode={darkMode}
                            onSuccess={async (data) => {
                                setIsCreateModalOpen(false);
                                if (createConfig.onSuccess) {
                                    await createConfig.onSuccess(data);
                                }
                            }}
                            onCancel={() => setIsCreateModalOpen(false)}
                            renderExtraActions={createConfig.renderExtraActions}
                        />
                    </div>
                </Modal>
            )}
        </div>
    );
};

PageLayout.EmptyState = ({ icon, title, description, children, className }) => {
    return (
        <div className={cn(
            "col-span-full py-20 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-[40px]",
            className
        )}>
            {icon && <div className="flex justify-center mb-4">{icon}</div>}
            <h3 className="text-lg font-bold text-slate-400">{title}</h3>
            {description && <p className="text-slate-500 text-sm">{description}</p>}
            {children}
        </div>
    );
};

export default PageLayout;
