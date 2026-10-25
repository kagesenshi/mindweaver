import React, { useState } from 'react';
import { Terminal, RefreshCcw, Zap, AlertCircle, Loader2, Activity, Clock, Copy, Check } from 'lucide-react';
import { cn } from '../utils/cn';
import DynamicForm from './DynamicForm';
import ResourceConfirmModal from './ResourceConfirmModal';
import PageLayout from './PageLayout';
import Drawer from './Drawer';
import Modal from './Modal';

const StatusBadge = ({ status }) => {
    const styles = {
        running: 'mw-badge-success',
        online: 'mw-badge-success',
        connected: 'mw-badge-success',
        warning: 'mw-badge-warning',
        pending: 'mw-badge-warning',
        stopped: 'mw-badge-neutral',
        offline: 'mw-badge-neutral',
        error: 'mw-badge-danger',
        active: 'mw-badge-info',
    };
    return (
        <span className={cn(styles[status] || 'mw-badge-neutral')}>
            {(status || 'unknown').toUpperCase()}
        </span>
    );
};

const PlatformServiceView = ({
    darkMode,
    selectedPlatform,
    platformState,
    onBack,
    initialTab = 'connect',
    onRefresh,
    isRefreshing,
    onToggleActive,
    onDecommission,
    onDelete,
    deleteTitle = "Delete Cluster",
    deleteWarningText = "Permanently delete this cluster and all associated configurations. The cluster must be decommissioned before it can be deleted. This action cannot be undone.",
    deleteModalTitle = "Confirm Deletion",
    deleteButtonText = "DELETE CLUSTER",
    availableActions = [],
    isExecutingAction,
    onExecuteAction,
    icon: Icon,
    iconClassName = "text-blue-400",
    entityPath,
    fetchPlatforms,
    renderConnectTab,
    decommissionWarningText = "Decommissioning this cluster will permanently delete all associated Kubernetes resources and data. This action cannot be undone.",
    notDeployedTitle = "Cluster Not Deployed",
    notDeployedDescription = "Deploy the cluster to see connection details and access endpoints.",
    deployButtonText = "DEPLOY CLUSTER",
}) => {
    const [activeTab, setActiveTab] = useState(initialTab);
    const [isDecommissionModalOpen, setIsDecommissionModalOpen] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
    const [copied, setCopied] = useState(false);

    const formatTimestamp = (ts) => {
        if (!ts) return null;
        try {
            const d = new Date(ts);
            if (isNaN(d.getTime())) return String(ts);
            return d.toLocaleString();
        } catch {
            return String(ts);
        }
    };

    const statusTimestamp = platformState?.last_heartbeat || platformState?.modified || platformState?.created;

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="mw-page-header">
                <div className="flex gap-4 items-center min-w-0">
                    <div className={cn("mw-icon-box w-16 h-16 shrink-0", iconClassName)}>
                        {Icon && <Icon size={32} />}
                    </div>
                    <div className="min-w-0">
                        <div className="flex items-center gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{selectedPlatform.title}</h2>
                            <StatusBadge status={platformState?.status || (platformState?.active ? 'active' : 'stopped')} />
                        </div>
                        <div className="flex flex-wrap items-center gap-4 mt-2">
                            <span className="flex items-center gap-1.5 text-sm text-slate-400 shrink-0">
                                Instance ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedPlatform.id}</span>
                            </span>
                            <span className="flex items-center gap-1.5 text-sm text-slate-500 font-mono shrink-0">
                                <Terminal size={14} /> {selectedPlatform.image}
                            </span>
                            {platformState?.message && (
                                <button
                                    type="button"
                                    onClick={() => setIsStatusModalOpen(true)}
                                    className="flex items-center gap-1.5 text-sm text-slate-400 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700/80 px-2.5 py-0.5 rounded transition-colors cursor-pointer max-w-xs sm:max-w-sm md:max-w-md min-w-0 text-left border border-transparent hover:border-slate-300 dark:hover:border-slate-700"
                                    title="Click to view status details"
                                >
                                    {platformState.status === 'pending' ? (
                                        <Loader2 size={14} className="text-blue-500 animate-spin shrink-0" />
                                    ) : (
                                        <Activity size={14} className="text-blue-500 shrink-0" />
                                    )}
                                    <span className="truncate min-w-0">{platformState.message}</span>
                                </button>
                            )}
                        </div>
                    </div>
                </div>
                <div className="flex gap-3 shrink-0">
                    {availableActions.length > 0 && (
                        <Drawer
                            darkMode={darkMode}
                            trigger={({ isOpen }) => (
                                <button className={cn(
                                    "mw-btn-secondary px-6 py-2.5 flex items-center gap-2 min-w-[140px]",
                                    isOpen && "bg-slate-100 dark:bg-slate-800"
                                )}>
                                    <Zap size={16} className="text-blue-500" />
                                    <span>ACTIONS</span>
                                </button>
                            )}
                        >
                            <div className="flex flex-col min-w-[200px]">
                                {availableActions.map(action => (
                                    <button
                                        key={action}
                                        onClick={() => onExecuteAction(action)}
                                        disabled={isExecutingAction === action}
                                        className="w-full text-left px-5 py-3.5 text-xs font-bold uppercase tracking-widest hover:bg-slate-100/50 dark:hover:bg-slate-800/50 transition-all flex items-center justify-between group first:rounded-t-lg last:rounded-b-lg border-b last:border-b-0 border-slate-100 dark:border-slate-800/50"
                                    >
                                        <span className="text-slate-700 dark:text-slate-300 group-hover:text-blue-500">{action}</span>
                                        {isExecutingAction === action ? (
                                            <Loader2 size={14} className="animate-spin text-blue-500" />
                                        ) : (
                                            <Zap size={14} className="text-slate-400 group-hover:text-blue-500 opacity-60 group-hover:opacity-100 transition-all" />
                                        )}
                                    </button>
                                ))}
                            </div>
                        </Drawer>
                    )}
                    <button
                        onClick={onRefresh}
                        disabled={isRefreshing}
                        className="mw-btn-secondary px-6 py-2.5 flex items-center gap-2"
                    >
                        <RefreshCcw size={16} className={isRefreshing ? 'animate-spin' : ''} />
                        {isRefreshing ? 'REFRESHING...' : 'REFRESH'}
                    </button>
                    <button
                        onClick={onBack}
                        className="mw-btn-secondary px-6 py-2.5"
                    >
                        BACK TO LIST
                    </button>
                </div>
            </div>

            <div className="space-y-6">
                <div className={cn("flex items-center gap-4 border-b p-1", darkMode ? 'border-slate-800' : 'border-slate-200')}>
                    <button
                        onClick={() => setActiveTab('connect')}
                        className={cn(
                            "px-4 py-2 text-sm font-bold uppercase tracking-widest transition-all border-b-2",
                            activeTab === 'connect' ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                        )}
                    >
                        Connection & Access
                    </button>
                    <button
                        onClick={() => setActiveTab('configure')}
                        className={cn(
                            "px-4 py-2 text-sm font-bold uppercase tracking-widest transition-all border-b-2",
                            activeTab === 'configure' ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                        )}
                    >
                        Configuration
                    </button>
                    <button
                        onClick={() => setActiveTab('admin')}
                        className={cn(
                            "px-4 py-2 text-sm font-bold uppercase tracking-widest transition-all border-b-2",
                            activeTab === 'admin' ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                        )}
                    >
                        Administrative
                    </button>
                </div>

                {activeTab === 'connect' ? (
                    <div className="space-y-6 animate-in fade-in duration-500">
                        {!platformState?.active ? (
                            <PageLayout.EmptyState
                                icon={<Zap size={40} />}
                                title={notDeployedTitle}
                                description={notDeployedDescription}
                                className="p-12 bg-slate-50/50 dark:bg-slate-950/20"
                            >
                                <div className="flex justify-center w-full">
                                    <button
                                        onClick={onToggleActive}
                                        className="mw-btn-primary px-8 py-3 flex items-center justify-center gap-2 text-base mt-6"
                                    >
                                        <Zap size={18} /> {deployButtonText}
                                    </button>
                                </div>
                            </PageLayout.EmptyState>
                        ) : (
                            renderConnectTab()
                        )}
                    </div>
                ) : activeTab === 'configure' ? (
                    <div className="mw-panel animate-in fade-in slide-in-from-top-4 duration-500">
                        <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg"><Zap size={18} /></div>
                                <h4 className="text-base font-bold tracking-wider leading-none text-slate-900 dark:text-white">Configuration</h4>
                            </div>
                        </div>
                        <div className="p-8">
                            <DynamicForm
                                entityPath={entityPath}
                                mode="edit"
                                initialData={selectedPlatform}
                                darkMode={darkMode}
                                onCancel={() => setActiveTab('connect')}
                                onSuccess={async () => {
                                    await new Promise(resolve => setTimeout(resolve, 500));
                                    await fetchPlatforms();
                                    setActiveTab('connect');
                                }}
                            />
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6 animate-in fade-in slide-in-from-top-4 duration-500">
                        <div className="mw-panel overflow-hidden border-rose-500/20">
                            <div className="p-4 border-b bg-rose-500/5 border-rose-500/10 flex items-center gap-3">
                                <AlertCircle className="text-rose-500" size={20} />
                                <h4 className="text-base font-bold tracking-wider text-rose-500 uppercase">Danger Zone</h4>
                            </div>
                            <div className="p-8 space-y-6">
                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                                    <div className="space-y-1">
                                        <h5 className="text-lg font-bold text-slate-900 dark:text-white">Decommission Cluster</h5>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl">
                                            {decommissionWarningText}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => setIsDecommissionModalOpen(true)}
                                        disabled={!platformState?.active}
                                        className={cn(
                                            "px-8 py-3 rounded-xl font-bold text-sm transition-all border shrink-0",
                                            platformState?.active
                                                ? "bg-rose-500 text-white hover:bg-rose-600 border-rose-600 shadow-lg shadow-rose-500/20"
                                                : "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
                                        )}
                                    >
                                        DECOMMISSION CLUSTER
                                    </button>
                                </div>

                                {onDelete && (
                                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pt-6 border-t border-rose-500/10">
                                        <div className="space-y-1">
                                            <h5 className="text-lg font-bold text-slate-900 dark:text-white">{deleteTitle}</h5>
                                            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl">
                                                {deleteWarningText}
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => setIsDeleteModalOpen(true)}
                                            disabled={platformState?.active}
                                            className={cn(
                                                "px-8 py-3 rounded-xl font-bold text-sm transition-all border shrink-0",
                                                !platformState?.active
                                                    ? "bg-rose-500 text-white hover:bg-rose-600 border-rose-600 shadow-lg shadow-rose-500/20"
                                                    : "bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed"
                                            )}
                                        >
                                            {deleteButtonText}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
            {isDecommissionModalOpen && (
                <ResourceConfirmModal
                    isOpen={isDecommissionModalOpen}
                    onClose={() => setIsDecommissionModalOpen(false)}
                    onConfirm={(name, options) => onDecommission(name || selectedPlatform?.name, options)}
                    resourceName={selectedPlatform?.name}
                    darkMode={darkMode}
                    title="Confirm Decommissioning"
                    message={decommissionWarningText}
                    confirmText="DECOMMISSION"
                    icon={Icon}
                    variant="danger"
                    showForceOption={true}
                />
            )}
            {isDeleteModalOpen && (
                <ResourceConfirmModal
                    isOpen={isDeleteModalOpen}
                    onClose={() => setIsDeleteModalOpen(false)}
                    onConfirm={(name) => onDelete(name || selectedPlatform?.name)}
                    resourceName={selectedPlatform?.name}
                    darkMode={darkMode}
                    title={deleteModalTitle}
                    message={deleteWarningText}
                    confirmText="DELETE"
                    icon={Icon}
                    variant="danger"
                />
            )}
            {isStatusModalOpen && (
                <Modal
                    isOpen={isStatusModalOpen}
                    onClose={() => setIsStatusModalOpen(false)}
                    title="Service Status Details"
                    maxWidth="max-w-2xl"
                >
                    <div className="space-y-4">
                        <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800">
                            <div className="flex items-center gap-3">
                                <StatusBadge status={platformState?.status || (platformState?.active ? 'active' : 'stopped')} />
                                <span className="text-sm font-semibold text-slate-800 dark:text-white">
                                    {selectedPlatform.title}
                                </span>
                            </div>
                            {statusTimestamp && (
                                <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
                                    <Clock size={14} className="text-slate-400 shrink-0" />
                                    <span>Time set: {formatTimestamp(statusTimestamp)}</span>
                                </div>
                            )}
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className="text-xs uppercase tracking-wider font-semibold text-slate-500">
                                    Message
                                </label>
                                <button
                                    type="button"
                                    onClick={() => {
                                        if (platformState?.message) {
                                            navigator.clipboard.writeText(platformState.message);
                                            setCopied(true);
                                            setTimeout(() => setCopied(false), 2000);
                                        }
                                    }}
                                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                                    title="Copy message"
                                >
                                    {copied ? <Check size={13} className="text-emerald-500" /> : <Copy size={13} />}
                                    <span>{copied ? 'Copied' : 'Copy'}</span>
                                </button>
                            </div>
                            <div className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-sm border border-slate-800 whitespace-pre-wrap break-words max-h-96 overflow-y-auto selection:bg-blue-500 selection:text-white">
                                {platformState?.message}
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 pt-2">
                            <button
                                type="button"
                                onClick={() => setIsStatusModalOpen(false)}
                                className="mw-btn-secondary px-5 py-2 text-sm"
                            >
                                CLOSE
                            </button>
                        </div>
                    </div>
                </Modal>
            )}
        </div >
    );
};

export default PlatformServiceView;
