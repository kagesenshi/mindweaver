import React, { useState, useEffect } from 'react';
import { Server } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock, CredentialBlock } from '../../components/ServiceBlocks';

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

        let trinoUriObj = null;
        if (platformState?.trino_uri) {
            try {
                trinoUriObj = new URL(platformState.trino_uri);
            } catch (e) {
                console.error("Failed to parse trino_uri:", e);
            }
        }

        const ports = [];
        if (trinoUriObj) {
            const hostname = trinoUriObj.hostname;
            const port = trinoUriObj.port ? parseInt(trinoUriObj.port) : (trinoUriObj.protocol === 'https:' ? 443 : 80);
            const scheme = trinoUriObj.protocol.replace(':', '');
            const ingressDomain = platformState?.extra_data?.ingress_domain;

            if (ingressDomain && hostname.endsWith(ingressDomain)) {
                ports.push({
                    label: 'Trino UI / API (Envoy Ingress)',
                    load_balancer_ips: [hostname],
                    port: port,
                    scheme: scheme
                });
            } else {
                ports.push({
                    label: 'Trino UI / API (NodePort)',
                    node_port: port,
                    scheme: scheme
                });
            }
        }

        const externalUri = platformState?.trino_uri || (trinoUriObj ? trinoUriObj.toString() : null);

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={Server}
                        endpoints={endpoints}
                    />
                )}

                {ports.length > 0 && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={ports}
                        clusterNodes={platformState.cluster_nodes}
                        cliInfo={{
                            command: `trino --server ${externalUri || 'https://[NODE_IP]:[NODE_PORT]'} --catalog ${platformState?.extra_data?.preferred_catalog || 'hive'} --schema default`,
                            languageButtons: []
                        }}
                    />
                )}

                {platformState?.db_pass && (
                    <CredentialBlock
                        darkMode={darkMode}
                        credentials={[
                            { label: 'Trino Admin Password', value: platformState?.db_pass, isMasked: true },
                            ...(platformState?.ranger_pass ? [
                                { label: 'Ranger User Password', value: platformState?.ranger_pass, isMasked: true }
                            ] : [])
                        ]}
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
