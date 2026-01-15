import React from 'react';
import { Search } from 'lucide-react';
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

            {children}
        </div>
    );
};

export default PageLayout;
