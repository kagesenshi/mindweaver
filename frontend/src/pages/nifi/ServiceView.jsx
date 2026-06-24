// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState, useEffect } from 'react';
import { Network } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock } from '../../components/ServiceBlocks';

/**
 * ServiceView displays detail, status, and connection options for a single Apache NiFi platform instance.
 */
const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    nifi
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = nifi;
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

        // Internal Service Access
        if (selectedPlatform && platformState?.extra_data?.namespace) {
            const svcName = platformState.extra_data.service_name || `${selectedPlatform.name}-nifi-service`;
            const ns = platformState.extra_data.namespace;
            endpoints.push({
                title: 'NiFi Service endpoint',
                code: `http://${svcName}.${ns}.svc.cluster.local:8080`,
                description: 'Internal NiFi UI endpoint for in-cluster client applications.'
            });
        }

        // External access — build ports array from nifi_uri (ingress) or node_ports
        const ports = [];
        let nifiUriObj = null;
        if (platformState?.nifi_uri) {
            try {
                nifiUriObj = new URL(platformState.nifi_uri);
            } catch (e) {
                console.error('Failed to parse nifi_uri:', e);
            }
        }

        const ingressDomain = platformState?.extra_data?.ingress_domain;
        let isIngressUsed = false;

        if (nifiUriObj && ingressDomain && nifiUriObj.hostname.endsWith(ingressDomain)) {
            ports.push({
                label: 'NiFi Web UI (Envoy Ingress)',
                load_balancer_ips: [nifiUriObj.hostname],
                port: nifiUriObj.port ? parseInt(nifiUriObj.port) : (nifiUriObj.protocol === 'https:' ? 443 : 80),
                scheme: nifiUriObj.protocol.replace(':', '')
            });
            isIngressUsed = true;
        }

        const httpPort = platformState?.node_ports?.find(np => np.port === 8080);
        if (httpPort) {
            ports.push({
                label: 'NiFi Web UI (NodePort)',
                node_port: httpPort.node_port,
                scheme: nifiUriObj ? nifiUriObj.protocol.replace(':', '') : 'http'
            });
        } else if (!isIngressUsed && nifiUriObj) {
            ports.push({
                label: 'NiFi Web UI (NodePort)',
                node_port: nifiUriObj.port ? parseInt(nifiUriObj.port) : 8080,
                scheme: nifiUriObj.protocol.replace(':', '')
            });
        }

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={Network}
                        endpoints={endpoints}
                    />
                )}
                {ports.length > 0 && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={ports}
                        clusterNodes={platformState?.cluster_nodes}
                        icon={Network}
                        iconColorClass="text-orange-400"
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
            icon={Network}
            iconClassName="text-orange-400"
            entityPath="/platform/nifi"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. Ensure no services depend on this cluster before decommissioning."
            notDeployedTitle="Apache NiFi Not Deployed"
            notDeployedDescription="Deploy Apache NiFi to see connection endpoints."
            deployButtonText="DEPLOY NIFI"
        />
    );
};

export default ServiceView;
