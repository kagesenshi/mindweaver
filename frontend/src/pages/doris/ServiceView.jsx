/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React, { useState, useEffect } from 'react';
import { Database } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock, CredentialBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    doris
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = doris;
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
        const ns = platformState?.extra_data?.namespace || 'default';
        if (selectedPlatform) {
            endpoints.push({
                title: 'MySQL Protocol (Direct)',
                subtitle: 'Internal Only',
                code: `${selectedPlatform.name}-fe-service.${ns}.svc.cluster.local:9030`,
                description: 'Internal MySQL query port (9030) for connecting applications and analytics engines.'
            });
            endpoints.push({
                title: 'Frontend Web UI / REST',
                subtitle: 'Internal Only',
                code: `http://${selectedPlatform.name}-fe-service.${ns}.svc.cluster.local:8030`,
                description: 'Internal HTTP endpoint for Web Console and Stream Load operations.'
            });
        }

        const ports = [];
        let isIngressUsed = false;
        const ingressDomain = platformState?.extra_data?.ingress_domain;

        if (ingressDomain) {
            ports.push({
                label: 'Web UI (Ingress)',
                port: 443,
                scheme: 'https',
                url: `https://${selectedPlatform.name}.${ingressDomain}`
            });
            isIngressUsed = true;
        }

        if (platformState?.node_ports && platformState.node_ports.length > 0) {
            platformState.node_ports.forEach(np => {
                ports.push({
                    label: np.port === 9030 ? 'MySQL Query' : (np.port === 8030 ? 'Web UI' : np.name),
                    node_port: np.node_port,
                    port: np.port,
                    scheme: np.port === 8030 ? 'http' : (np.port === 443 ? 'https' : undefined),
                });
            });
        }

        const mysqlNodePort = platformState?.node_ports?.find(np => np.port === 9030);
        const nodeIp = platformState?.cluster_nodes?.[0]?.ipv4 || '[NODE_IP]';
        const cliInfo = mysqlNodePort ? {
            command: `mysql -h ${nodeIp} -P ${mysqlNodePort.node_port} -u root -p`,
            languageButtons: []
        } : null;

        const adminPassword = platformState?.db_pass || platformState?.admin_password || selectedPlatform.admin_password;

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={Database}
                        endpoints={endpoints}
                    />
                )}

                {ports.length > 0 && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={ports}
                        clusterNodes={platformState?.cluster_nodes || []}
                        cliInfo={cliInfo}
                        isIngressUsed={isIngressUsed}
                        icon={Database}
                    />
                )}

                {adminPassword && (
                    <CredentialBlock
                        darkMode={darkMode}
                        credentials={[
                            { label: 'Admin Username', value: platformState?.db_user || platformState?.admin_user || 'root' },
                            { label: 'Admin Password', value: adminPassword, isMasked: true },
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
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
            onToggleActive={toggleActive}
            onDecommission={handleDecommission}
            icon={Database}
            iconClassName="text-cyan-400"
            entityPath="/platform/doris"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            initialTab={initialTab}
            decommissionWarningText="Permanently delete all associated Kubernetes resources and data for this Doris cluster. This action cannot be undone."
            notDeployedTitle="Apache Doris Not Deployed"
            notDeployedDescription="Deploy the Apache Doris cluster to start querying and access the web console."
            deployButtonText="DEPLOY DORIS"
        />
    );
};

export default ServiceView;
