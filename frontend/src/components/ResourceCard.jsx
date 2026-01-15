import React from 'react';
import { Edit2, Trash2 } from 'lucide-react';
import { cn } from '../utils/cn';

const StatusBadge = ({ status }) => {
    const styles = {
        running: 'mw-badge-success',
        connected: 'mw-badge-success',
        active: 'mw-badge-success',
        warning: 'mw-badge-warning',
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
    onEdit,
    onDelete,
    onClick,
    isActive = false,
    children,
    footer,
    className
}) => {
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
                        <h4 className="text-lg font-bold truncate text-slate-900 dark:text-white uppercase leading-tight">
                            {title}
                        </h4>
                        {subtitle && (
                            <p className="text-sm text-slate-500 font-mono uppercase mt-1 truncate">
                                {subtitle}
                            </p>
                        )}
                    </div>
                </div>
                {status && <StatusBadge status={status} />}
            </div>

            {children && (
                <div className="flex-1">
                    {children}
                </div>
            )}

            {(footer || onEdit || onDelete) && (
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800/50 flex items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                        {footer}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                        {onEdit && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onEdit();
                                }}
                                className="mw-btn-icon opacity-0 group-hover:opacity-100 transition-opacity p-2"
                                title="Edit"
                            >
                                <Edit2 size={16} />
                            </button>
                        )}
                        {onDelete && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDelete();
                                }}
                                className="mw-btn-icon-danger opacity-0 group-hover:opacity-100 transition-opacity p-2"
                                title="Delete"
                            >
                                <Trash2 size={16} />
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ResourceCard;
