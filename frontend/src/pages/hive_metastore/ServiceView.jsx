import React, { useState, useEffect } from 'react';
import {
    Boxes, Server, Settings, Activity, Terminal, RefreshCcw, Zap, Lock,
    Eye, EyeOff, Copy, AlertCircle, Loader2, Database, Globe
} from 'lucide-react';
import { cn } from '../../utils/cn';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import ResourceConfirmModal from '../../components/ResourceConfirmModal';
import PageLayout from '../../components/PageLayout';
import Drawer from '../../components/Drawer';
import { useNotification } from '../../providers/NotificationProvider';

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

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    hms
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = hms;
    const [platformState, setPlatformState] = useState(null);
    const [activeTab, setActiveTab] = useState(initialTab);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [isDecommissionModalOpen, setIsDecommissionModalOpen] = useState(false);

    const { showSuccess, showError } = useNotification();

    useEffect(() => {
        let timer;
        if (selectedPlatformId) {
            getPlatformState(selectedPlatformId).then(setPlatformState);
            timer = setInterval(() => {
                getPlatformState(selectedPlatformId).then(setPlatformState);
            }, 15000);
        } else {
            setPlatformState(null);
        }
        return () => {
            if (timer) clearInterval(timer);
        };
    }, [selectedPlatformId, getPlatformState]);

    const handleRefresh = async () => {
        if (!selectedPlatformId) return;
        setIsRefreshing(true);
        try {
            const updated = await refreshPlatformState(selectedPlatformId);
            setPlatformState(updated);
            showSuccess("Status refreshed");
        } finally {
            setIsRefreshing(false);
        }
    };

    const toggleActive = async () => {
        if (!selectedPlatformId || !platformState) return;
        if (platformState.active) {
            setIsDecommissionModalOpen(true);
        } else {
            setPlatformState({ ...platformState, active: true, status: 'pending', message: 'Triggering deployment...' });
            try {
                const response = await updatePlatformState(selectedPlatformId, { active: true });
                if (response) setPlatformState(response);
                await handleRefresh();
            } catch (err) {
                showError(`Failed to trigger deployment: ${err.message}`);
                const original = await getPlatformState(selectedPlatformId);
                setPlatformState(original);
            }
        }
    };

    const handleDecommission = async (name) => {
        if (!selectedPlatformId) return;
        setPlatformState({ ...platformState, active: false, status: 'offline', message: 'Decommissioning...' });
        setIsDecommissionModalOpen(false);
        try {
            const response = await updatePlatformState(selectedPlatformId, { active: false }, { 'X-RESOURCE-NAME': name });
            if (response) setPlatformState(response);
            await handleRefresh();
        } catch (err) {
            showError(`Failed to decommission: ${err.message}`);
            const original = await getPlatformState(selectedPlatformId);
            setPlatformState(original);
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="mw-page-header">
                <div className="flex gap-4 items-center">
                    <div className="mw-icon-box w-16 h-16 text-indigo-400">
                        <Boxes size={32} />
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
                        </div>
                    </div>
                </div>
                <div className="flex gap-3">
                    <button onClick={handleRefresh} disabled={isRefreshing} className="mw-btn-secondary px-6 py-2.5 flex items-center gap-2">
                        <RefreshCcw size={16} className={isRefreshing ? 'animate-spin' : ''} />
                        {isRefreshing ? 'REFRESHING...' : 'REFRESH'}
                    </button>
                    <button onClick={onBack} className="mw-btn-secondary px-6 py-2.5">BACK TO LIST</button>
                </div>
            </div>

            <div className="space-y-6">
                <div className={cn("flex items-center gap-4 border-b p-1", darkMode ? 'border-slate-800' : 'border-slate-200')}>
                    {['connect', 'configure', 'admin'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={cn(
                                "px-4 py-2 text-sm font-bold uppercase tracking-widest transition-all border-b-2",
                                activeTab === tab ? 'border-blue-500 text-blue-500' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                            )}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>

                {activeTab === 'connect' ? (
                    <div className="space-y-6 animate-in fade-in duration-500">
                        {!platformState?.active ? (
                            <PageLayout.EmptyState
                                icon={<Zap size={40} />}
                                title="Metastore Not Deployed"
                                description="Deploy the metastore to see connection endpoints."
                                className="p-12 bg-slate-50/50 dark:bg-slate-950/20"
                            >
                                <button onClick={toggleActive} className="mw-btn-primary px-8 py-3 flex items-center gap-2 text-base mt-6">
                                    <Zap size={18} /> DEPLOY METASTORE
                                </button>
                            </PageLayout.EmptyState>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="mw-panel">
                                    <div className="p-4 border-b flex items-center gap-3 bg-slate-50 dark:bg-slate-950/30">
                                        <Database className="text-blue-500" size={18} />
                                        <h4 className="text-base font-bold text-slate-900 dark:text-white">HMS Endpoint</h4>
                                    </div>
                                    <div className="p-6">
                                        <div className="p-4 bg-slate-900 rounded-xl group relative">
                                            <code className="text-blue-400 font-mono text-sm">{platformState?.hms_uri || 'Resolving...'}</code>
                                            <button onClick={() => navigator.clipboard.writeText(platformState?.hms_uri || '')} className="absolute right-4 top-4 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition-all">
                                                <Copy size={16} />
                                            </button>
                                        </div>
                                        <p className="mt-4 text-sm text-slate-500">Thrift URI for Spark/Trino configuration.</p>
                                    </div>
                                </div>

                                {selectedPlatform.iceberg_enabled && (
                                    <div className="mw-panel">
                                        <div className="p-4 border-b flex items-center gap-3 bg-slate-50 dark:bg-slate-950/30">
                                            <Globe className="text-emerald-500" size={18} />
                                            <h4 className="text-base font-bold text-slate-900 dark:text-white">Iceberg REST Endpoint</h4>
                                        </div>
                                        <div className="p-6">
                                            <div className="p-4 bg-slate-900 rounded-xl group relative">
                                                <code className="text-emerald-400 font-mono text-sm">{platformState?.iceberg_uri || 'Resolving...'}</code>
                                                <button onClick={() => navigator.clipboard.writeText(platformState?.iceberg_uri || '')} className="absolute right-4 top-4 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition-all">
                                                    <Copy size={16} />
                                                </button>
                                            </div>
                                            <p className="mt-4 text-sm text-slate-500">REST Catalog endpoint for Iceberg clients.</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ) : activeTab === 'configure' ? (
                    <div className="mw-panel animate-in fade-in slide-in-from-top-4 duration-500">
                        <div className="p-4 border-b bg-slate-50 dark:bg-slate-950/30">
                            <h4 className="text-base font-bold text-slate-900 dark:text-white">Metastore Configuration</h4>
                        </div>
                        <div className="p-8">
                            <DynamicForm
                                entityPath="/platform/hive-metastore"
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
                    <div className="mw-panel border-rose-500/20">
                        <div className="p-4 border-b bg-rose-500/5 border-rose-500/10 flex items-center gap-3">
                            <AlertCircle className="text-rose-500" size={20} />
                            <h4 className="text-base font-bold text-rose-500 uppercase">Danger Zone</h4>
                        </div>
                        <div className="p-8 flex items-center justify-between">
                            <div>
                                <h5 className="text-lg font-bold text-slate-900 dark:text-white">Decommission Metastore</h5>
                                <p className="text-sm text-slate-500 max-w-md">Permanently delete all associated resources. This cannot be undone.</p>
                            </div>
                            <button onClick={toggleActive} disabled={!platformState?.active} className={cn("px-8 py-3 rounded-xl font-bold text-sm transition-all border", platformState?.active ? "bg-rose-500 text-white hover:bg-rose-600 border-rose-600" : "bg-slate-100 text-slate-400 cursor-not-allowed")}>
                                DECOMMISSION
                            </button>
                        </div>
                    </div>
                )}
            </div>
            {isDecommissionModalOpen && (
                <ResourceConfirmModal
                    isOpen={isDecommissionModalOpen}
                    onClose={() => setIsDecommissionModalOpen(false)}
                    onConfirm={handleDecommission}
                    resourceName={selectedPlatform?.name}
                    darkMode={darkMode}
                    title="Confirm Decommissioning"
                    message="This will delete the Hive Metastore cluster."
                    confirmText="DECOMMISSION"
                    icon={Boxes}
                    variant="danger"
                />
            )}
        </div>
    );
};

export default ServiceView;
