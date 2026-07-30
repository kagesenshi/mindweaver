import React, { useState, useEffect } from 'react';
import { Activity, ExternalLink } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock, CredentialBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    airflow
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = airflow;
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
                title: 'Airflow Web UI',
                code: `http://${selectedPlatform.name}.${platformState.extra_data.namespace}.svc.cluster.local:8080`,
                description: 'Internal endpoint for accessing the Airflow web interface within the cluster.'
            });
        }

        let airflowUriObj = null;
        if (platformState?.airflow_uri) {
            try {
                airflowUriObj = new URL(platformState.airflow_uri);
            } catch (e) {
                console.error("Failed to parse airflow_uri:", e);
            }
        }

        const ports = [];
        const ingressDomain = platformState?.extra_data?.ingress_domain;

        if (airflowUriObj && ingressDomain && airflowUriObj.hostname.endsWith(ingressDomain)) {
            ports.push({
                label: 'Airflow Web UI (Envoy Ingress)',
                load_balancer_ips: [airflowUriObj.hostname],
                port: airflowUriObj.port ? parseInt(airflowUriObj.port) : (airflowUriObj.protocol === 'https:' ? 443 : 80),
                scheme: airflowUriObj.protocol.replace(':', '')
            });
        }

        const httpPort = platformState?.node_ports?.find(np => np.port === 8080);
        if (httpPort) {
            ports.push({
                label: 'Airflow Web UI (NodePort)',
                node_port: httpPort.node_port,
                scheme: airflowUriObj ? airflowUriObj.protocol.replace(':', '') : 'http'
            });
        }

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={Activity}
                        endpoints={endpoints}
                    />
                )}

                {ports.length > 0 && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={ports}
                        clusterNodes={platformState.cluster_nodes}
                        icon={Activity}
                        iconColorClass="text-cyan-500"
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
            icon={Activity}
            iconClassName="text-cyan-500"
            entityPath="/platform/airflow"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. This cannot be undone."
            notDeployedTitle="Airflow Not Deployed"
            notDeployedDescription="Deploy Airflow to see connection info and Access UI."
            deployButtonText="DEPLOY AIRFLOW"
        />
    );
};

export default ServiceView;
