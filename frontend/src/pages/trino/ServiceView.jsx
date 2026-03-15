import React, { useState, useEffect } from 'react';
import { Server } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    trino
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = trino;
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

    const renderConnectTab = () => {
        const endpoints = [];
        if (selectedPlatform && platformState?.extra_data?.namespace) {
            endpoints.push({
                title: 'Trino HTTPS Endpoint',
                code: `https://${selectedPlatform.name}.${platformState.extra_data.namespace}.svc.cluster.local:8443`,
                description: 'Internal HTTPS URI for connecting any Trino client.'
            });
        }

        const httpsPort = platformState?.node_ports?.find(np => np.name.endsWith('https-nodeport'));
        const externalUri = platformState?.trino_uri || (httpsPort && platformState.cluster_nodes?.[0]?.ipv4 ? `https://${platformState.cluster_nodes[0].ipv4}:${httpsPort.node_port}` : null);

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={Server}
                        endpoints={endpoints}
                    />
                )}

                {httpsPort && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={[{
                            label: 'Trino UI / API (HTTPS)',
                            node_port: httpsPort.node_port
                        }]}
                        clusterNodes={platformState.cluster_nodes}
                        cliInfo={{
                            command: `trino --server ${externalUri || 'https://[NODE_IP]:[NODE_PORT]'} --catalog ${platformState?.extra_data?.preferred_catalog || 'hive'} --schema default`,
                            languageButtons: []
                        }}
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
            icon={Server}
            iconClassName="text-cyan-500"
            entityPath="/platform/trino"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. This cannot be undone."
            notDeployedTitle="Trino Not Deployed"
            notDeployedDescription="Deploy Trino to see connection endpoints."
            deployButtonText="DEPLOY TRINO"
        />
    );
};

export default ServiceView;
