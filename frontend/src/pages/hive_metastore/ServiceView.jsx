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
