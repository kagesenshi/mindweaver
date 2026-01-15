import React from 'react';
import { Search, Loader2, Inbox } from 'lucide-react';
import { cn } from '../utils/cn';

const PageLayout = ({
    title,
    description,
    headerActions,
    searchQuery,
    onSearchChange,
    searchPlaceholder = "Search...",
    children,
    isLoading = false,
    isEmpty = false,
    emptyState = null,
    className
}) => {
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
                {headerActions && (
                    <div className="flex items-center gap-2">
                        {headerActions}
                    </div>
                )}
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
                emptyState ? (
                    React.isValidElement(emptyState) ? emptyState : (
                        <div className="col-span-full py-20 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-[40px]">
                            {emptyState.icon && <div className="flex justify-center mb-4">{emptyState.icon}</div>}
                            <h3 className="text-lg font-bold text-slate-400">{emptyState.title}</h3>
                            <p className="text-slate-500 text-sm">{emptyState.description}</p>
                        </div>
                    )
                ) : (
                    <div className="col-span-full py-20 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-[40px]">
                        <h3 className="text-lg font-bold text-slate-400">No items found</h3>
                        <p className="text-slate-500 text-sm">There are no items to display.</p>
                    </div>
                )
            ) : (
                children
            )}
        </div>
    );
};

export default PageLayout;
