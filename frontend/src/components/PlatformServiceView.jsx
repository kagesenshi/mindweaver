import React, { useState } from 'react';
import { Terminal, RefreshCcw, Zap, AlertCircle, Loader2, Activity } from 'lucide-react';
import { cn } from '../utils/cn';
import DynamicForm from './DynamicForm';
import ResourceConfirmModal from './ResourceConfirmModal';
import PageLayout from './PageLayout';
import Drawer from './Drawer';

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

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="mw-page-header">
                <div className="flex gap-4 items-center">
                    <div className={cn("mw-icon-box w-16 h-16", iconClassName)}>
                        {Icon && <Icon size={32} />}
                    </div>
                    <div>
                        <div className="flex items-center gap-3">
                            <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">{selectedPlatform.title}</h2>
                            <StatusBadge status={platformState?.status || (platformState?.active ? 'active' : 'stopped')} />
                        </div>
                        <div className="flex items-center gap-4 mt-2">
                            <span className="flex items-center gap-1.5 text-sm text-slate-400">
                                Instance ID: <span className="text-slate-500 font-mono font-bold uppercase tracking-tight">{selectedPlatform.id}</span>
                            </span>
                            <span className="flex items-center gap-1.5 text-sm text-slate-500 font-mono">
                                <Terminal size={14} /> {selectedPlatform.image}
                            </span>
                            {platformState?.message && (
                                <span className="flex items-center gap-1.5 text-sm text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                                    {platformState.status === 'pending' ? (
                                        <Loader2 size={14} className="text-blue-500 animate-spin" />
                                    ) : (
                                        <Activity size={14} className="text-blue-500" />
                                    )}
                                    <span>{platformState.message}</span>
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                <div className="flex gap-3">
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
                            </div>
                        </div>
                    </div>
                )}
            </div>
            {isDecommissionModalOpen && (
                <ResourceConfirmModal
                    isOpen={isDecommissionModalOpen}
                    onClose={() => setIsDecommissionModalOpen(false)}
                    onConfirm={() => onDecommission(selectedPlatform?.name)}
                    resourceName={selectedPlatform?.name}
                    darkMode={darkMode}
                    title="Confirm Decommissioning"
                    message={decommissionWarningText}
                    confirmText="DECOMMISSION"
                    icon={Icon}
                    variant="danger"
                />
            )}
        </div >
    );
};

export default PlatformServiceView;
