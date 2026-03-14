import React, { useState, useEffect } from 'react';
import { Boxes, Database, Globe, Copy } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';

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
    const [isRefreshing, setIsRefreshing] = useState(false);

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
    };

    const handleDecommission = async (name) => {
        if (!selectedPlatformId) return;
        setPlatformState({ ...platformState, active: false, status: 'offline', message: 'Decommissioning...' });
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

    const renderConnectTab = () => (
        <div className="space-y-6">
            {platformState?.extra_data?.namespace && (
                <div className="mw-panel">
                    <div className="p-4 border-b flex items-center gap-3 bg-slate-50 dark:bg-slate-950/30">
                        <Boxes className="text-emerald-500" size={18} />
                        <h4 className="text-base font-bold text-slate-900 dark:text-white">Internal Network Access</h4>
                    </div>
                    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="p-4 border rounded-xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 group relative">
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-2">Thrift HMS</p>
                            <div className="flex items-center justify-between">
                                <code className="text-xs font-mono text-emerald-600 dark:text-emerald-400 truncate px-1">
                                    thrift://{selectedPlatform.name}.{platformState.extra_data.namespace}.svc.cluster.local:9083
                                </code>
                                <button onClick={() => navigator.clipboard.writeText(`thrift://${selectedPlatform.name}.${platformState.extra_data.namespace}.svc.cluster.local:9083`)} className="p-1 text-slate-400 hover:text-emerald-500 transition-colors shrink-0" title="Copy internal endpoint"><Copy size={14} /></button>
                            </div>
                            <p className="mt-4 text-xs text-slate-500">Thrift URI for Spark/Trino configuration.</p>
                        </div>
                        {selectedPlatform.iceberg_enabled && (
                            <div className="p-4 border rounded-xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 group relative">
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-2">Iceberg REST</p>
                                <div className="flex items-center justify-between">
                                    <code className="text-xs font-mono text-emerald-600 dark:text-emerald-400 truncate px-1">
                                        http://{selectedPlatform.name}-iceberg.{platformState.extra_data.namespace}.svc.cluster.local:{selectedPlatform.iceberg_port}
                                    </code>
                                    <button onClick={() => navigator.clipboard.writeText(`http://${selectedPlatform.name}-iceberg.${platformState.extra_data.namespace}.svc.cluster.local:${selectedPlatform.iceberg_port}`)} className="p-1 text-slate-400 hover:text-emerald-500 transition-colors shrink-0" title="Copy internal endpoint"><Copy size={14} /></button>
                                </div>
                                <p className="mt-4 text-xs text-slate-500">REST Catalog endpoint for Iceberg clients.</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );

    return (
        <PlatformServiceView
            darkMode={darkMode}
            selectedPlatformId={selectedPlatformId}
            selectedPlatform={selectedPlatform}
            platformState={platformState}
            onBack={onBack}
            initialTab={initialTab}
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
            onToggleActive={toggleActive}
            onDecommission={handleDecommission}
            icon={Boxes}
            iconClassName="text-indigo-400"
            entityPath="/platform/hive-metastore"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. This cannot be undone."
            notDeployedTitle="Metastore Not Deployed"
            notDeployedDescription="Deploy the metastore to see connection endpoints."
            deployButtonText="DEPLOY METASTORE"
        />
    );
};

export default ServiceView;
