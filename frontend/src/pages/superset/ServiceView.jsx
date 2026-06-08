import React, { useState, useEffect } from 'react';
import { LayoutDashboard, ExternalLink } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock, CredentialBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    superset
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = superset;
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
                title: 'Superset Service',
                code: `http://${selectedPlatform.name}.${platformState.extra_data.namespace}.svc.cluster.local:8088`,
                description: 'Internal endpoint for connecting to Superset within the cluster.'
            });
        }

        let supersetUriObj = null;
        if (platformState?.superset_uri) {
            try {
                supersetUriObj = new URL(platformState.superset_uri);
            } catch (e) {
                console.error("Failed to parse superset_uri:", e);
            }
        }

        const ports = [];
        if (supersetUriObj) {
            const hostname = supersetUriObj.hostname;
            const port = supersetUriObj.port ? parseInt(supersetUriObj.port) : (supersetUriObj.protocol === 'https:' ? 443 : 80);
            const scheme = supersetUriObj.protocol.replace(':', '');
            const ingressDomain = platformState?.extra_data?.ingress_domain;

            if (ingressDomain && hostname.endsWith(ingressDomain)) {
                ports.push({
                    label: 'Superset UI (Envoy Ingress)',
                    load_balancer_ips: [hostname],
                    port: port,
                    scheme: scheme
                });
            } else {
                ports.push({
                    label: 'Superset UI (NodePort)',
                    node_port: port,
                    scheme: scheme
                });
            }
        }

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={LayoutDashboard}
                        endpoints={endpoints}
                    />
                )}

                {ports.length > 0 && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={ports}
                        clusterNodes={platformState.cluster_nodes}
                        icon={LayoutDashboard}
                        iconColorClass="text-indigo-500"
                    />
                )}

                {platformState?.admin_user && platformState?.admin_password && (
                    <CredentialBlock
                        darkMode={darkMode}
                        credentials={[
                            { label: 'Username', value: platformState?.admin_user },
                            { label: 'Password', value: platformState?.admin_password, isMasked: true }
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
            icon={LayoutDashboard}
            iconClassName="text-indigo-500"
            entityPath="/platform/superset"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. This cannot be undone."
            notDeployedTitle="Superset Not Deployed"
            notDeployedDescription="Deploy Superset to see connection info and Access UI."
            deployButtonText="DEPLOY SUPERSET"
        />
    );
};

export default ServiceView;
