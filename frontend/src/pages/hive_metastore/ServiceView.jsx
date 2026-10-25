import React, { useState, useEffect } from 'react';
import { Boxes } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    hms
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms, deletePlatform } = hms;
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

    const handleDecommission = async (name, options = {}) => {
        if (!selectedPlatformId) return;
        const force = Boolean(options?.force);
        setPlatformState({
            ...platformState,
            active: false,
            status: 'offline',
            message: force ? 'Force decommissioning...' : 'Decommissioning...'
        });
        try {
            const response = await updatePlatformState(
                selectedPlatformId,
                { active: false, force },
                { 'X-RESOURCE-NAME': name }
            );
            if (response) setPlatformState(response);
            showSuccess(force ? 'Hive Metastore cluster force-decommissioned successfully' : 'Hive Metastore cluster decommissioned successfully');
            await handleRefresh();
        } catch (err) {
            let errorMsg = err.message;
            if (err.response?.data?.detail) {
                const detail = err.response.data.detail;
                if (Array.isArray(detail) && detail.length > 0) {
                    errorMsg = detail[0].msg || errorMsg;
                } else if (typeof detail === 'string') {
                    errorMsg = detail;
                }
            } else if (err.response?.data?.message) {
                errorMsg = err.response.data.message;
            }
            if (err.response?.status !== 422) {
                showError(`Failed to decommission: ${errorMsg}`);
            }
            const original = await getPlatformState(selectedPlatformId);
            setPlatformState(original);
        }
    };

    const handleDelete = async (name) => {
        if (!selectedPlatformId) return;
        try {
            await deletePlatform(selectedPlatformId, name);
            showSuccess('Hive Metastore cluster deleted successfully');
            if (onBack) onBack();
        } catch (err) {
            showError(`Failed to delete cluster: ${err.message}`);
        }
    };

    const renderConnectTab = () => {
        const endpoints = [];
        if (selectedPlatform && platformState?.extra_data?.namespace) {
            endpoints.push({
                title: 'Thrift HMS',
                code: `thrift://${selectedPlatform.name}.${platformState.extra_data.namespace}.svc.cluster.local:9083`,
                description: 'Thrift URI for Spark/Trino configuration.'
            });
            
            if (selectedPlatform.iceberg_enabled) {
                endpoints.push({
                    title: 'Iceberg REST',
                    code: `http://${selectedPlatform.name}-iceberg.${platformState.extra_data.namespace}.svc.cluster.local:9001/iceberg`,
                    description: 'REST Catalog endpoint for Iceberg clients.'
                });
            }
        }

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock 
                        darkMode={darkMode}
                        icon={Boxes}
                        endpoints={endpoints}
                    />
                )}
            </div>
        );
    };

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
            onDelete={handleDelete}
            deleteModalTitle="Delete Hive Metastore Cluster"
            deleteWarningText="Permanently delete this Hive Metastore cluster and all associated configurations. The cluster must be decommissioned before it can be deleted. This action cannot be undone."
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
