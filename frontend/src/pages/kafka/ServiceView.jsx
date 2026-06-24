// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState, useEffect } from 'react';
import { RefreshCcw } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    kafka
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = kafka;
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

        if (platformState?.kafka_url) {
            endpoints.push({
                title: 'Kafka Bootstrap Servers',
                code: platformState.kafka_url,
                description: 'Internal Kafka bootstrap connection string for client applications.'
            });
        } else if (selectedPlatform && platformState?.extra_data?.namespace) {
            const svcName = platformState.extra_data.service_name || selectedPlatform.name;
            const ns = platformState.extra_data.namespace;
            endpoints.push({
                title: 'Kafka Bootstrap Servers',
                code: `${svcName}.${ns}.svc.cluster.local:9092`,
                description: 'Internal Kafka bootstrap connection string for client applications.'
            });
        }

        const externalPort = platformState?.node_ports?.find(np => np.port === 9094 || np.name?.endsWith('-external-bootstrap'));

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={RefreshCcw}
                        endpoints={endpoints}
                    />
                )}

                {externalPort && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={[{
                            label: 'Kafka SSL NodePort',
                            node_port: externalPort.node_port
                        }]}
                        clusterNodes={platformState.cluster_nodes}
                        cliInfo={{
                            command: `kcat -b ${platformState.cluster_nodes?.[0]?.ipv4 || '[NODE_IP]'}:${externalPort.node_port} -L -X security.protocol=SSL`,
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
            icon={RefreshCcw}
            iconClassName="text-cyan-400"
            entityPath="/platform/kafka"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. Ensure no services depend on this cluster before decommissioning."
            notDeployedTitle="Apache Kafka Not Deployed"
            notDeployedDescription="Deploy Apache Kafka to see connection endpoints."
            deployButtonText="DEPLOY KAFKA"
        />
    );
};

export default ServiceView;
