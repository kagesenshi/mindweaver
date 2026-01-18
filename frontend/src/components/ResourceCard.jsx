import React, { useState } from 'react';
import { Edit2, Trash2 } from 'lucide-react';
import { cn } from '../utils/cn';
import ResourceConfirmModal from './ResourceConfirmModal';

const StatusBadge = ({ status }) => {
    const styles = {
        running: 'mw-badge-success',
        online: 'mw-badge-success',
        connected: 'mw-badge-success',
        active: 'mw-badge-success',
        warning: 'mw-badge-warning',
        pending: 'mw-badge-warning',
        stopped: 'mw-badge-neutral',
        error: 'mw-badge-danger',
        unknown: 'mw-badge-neutral'
    };

    const normalizedStatus = (status || 'unknown').toLowerCase();

    return (
        <span className={cn(styles[normalizedStatus] || 'mw-badge-neutral')}>
            {(status || 'unknown').toUpperCase()}
        </span>
    );
};

const ResourceCard = ({
    icon,
    title,
    subtitle,
    status,
    resourceName,
    darkMode,
    onEdit,
    onDelete,
    onClick,
    isActive = false,
    children,
    footer,
    className
}) => {
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    return (
        <div
            onClick={onClick}
            className={cn(
                "mw-card group flex flex-col transition-all duration-200",
                onClick && "cursor-pointer hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/5 dark:hover:shadow-blue-500/10",
                isActive && "border-blue-500 ring-1 ring-blue-500 bg-blue-500/5 dark:bg-blue-500/10",
                className
            )}
        >
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-4 min-w-0">
                    {icon && (
                        <div className={cn(
                            "mw-icon-box p-3 shrink-0",
                            isActive ? "text-blue-500 bg-blue-500/20" : "text-slate-500 group-hover:text-blue-500 transition-colors"
                        )}>
                            {icon}
                        </div>
                    )}
                    <div className="min-w-0">
                        <h4 className="text-lg font-bold truncate text-slate-900 dark:text-white leading-tight">
                            {title}
                        </h4>
                        {subtitle && (
                            <p className="text-base text-slate-500 font-mono mt-1 truncate">
                                {subtitle}
                            </p>
                        )}
                    </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                    {status && <StatusBadge status={status} />}
                    {(onEdit || onDelete) && (
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            {onEdit && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onEdit();
                                    }}
                                    className="p-1.5 text-slate-400 hover:text-blue-500 hover:bg-blue-500/10 rounded-lg transition-all"
                                    title="Edit"
                                >
                                    <Edit2 size={16} />
                                </button>
                            )}
                            {onDelete && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setIsDeleteModalOpen(true);
                                    }}
                                    className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 rounded-lg transition-all"
                                    title="Delete"
                                >
                                    <Trash2 size={16} />
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {children && (
                <div className="flex-1 mt-4 pt-4 border-t border-slate-200 dark:border-slate-800/50">
                    {children}
                </div>
            )}

            {footer && (
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800/50 flex items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                        {footer}
                    </div>
                </div>
            )}
            {isDeleteModalOpen && (
                <ResourceConfirmModal
                    isOpen={isDeleteModalOpen}
                    onClose={() => setIsDeleteModalOpen(false)}
                    onConfirm={(name) => onDelete(name)}
                    resourceName={resourceName || title}
                    darkMode={darkMode}
                    title="Confirm Deletion"
                    message="This action is permanent and cannot be undone. All data and resources associated with this resource will be destroyed."
                    confirmText="DELETE"
                    icon={Trash2}
                    variant="danger"
                />
            )}
        </div>
    );
};

export default ResourceCard;
