// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState, useEffect } from 'react';
import { ShieldCheck, ExternalLink } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock, CredentialBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    ranger
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = ranger;
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
                title: 'Ranger Admin UI',
                code: `https://${selectedPlatform.name}.${platformState.extra_data.namespace}.svc.cluster.local:6080`,
                description: 'Internal URI for Ranger Admin.'
            });
        }

        const ingressDomain = platformState?.extra_data?.ingress_domain;
        const httpPort = platformState?.node_ports?.find(np => np.port === 6080);

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={ShieldCheck}
                        endpoints={endpoints}
                    />
                )}
                {(ingressDomain || httpPort) && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={[
                            ...(ingressDomain ? [{
                                label: 'Ranger Admin UI (Envoy Ingress)',
                                load_balancer_ips: [`${selectedPlatform.name}.${ingressDomain}`],
                                port: 443,
                                scheme: 'https'
                            }] : []),
                            ...(httpPort ? [{
                                label: 'Ranger Admin UI (NodePort)',
                                node_port: httpPort.node_port,
                                scheme: 'https'
                            }] : [])
                        ]}
                        clusterNodes={platformState.cluster_nodes}
                        icon={ShieldCheck}
                        iconColorClass="text-blue-400"
                    />
                )}
                {platformState?.admin_password && (
                    <CredentialBlock
                        darkMode={darkMode}
                        credentials={[
                            { label: 'Admin Password', value: platformState?.admin_password, isMasked: true },
                            { label: 'KeyAdmin Password', value: platformState?.keyadmin_password, isMasked: true },
                            { label: 'TagSync Password', value: platformState?.tagsync_password, isMasked: true },
                            { label: 'UserSync Password', value: platformState?.usersync_password, isMasked: true }
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
            icon={ShieldCheck}
            iconClassName="text-blue-400"
            entityPath="/platform/ranger"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. This cannot be undone."
            notDeployedTitle="Ranger Not Deployed"
            notDeployedDescription="Deploy Ranger to see connection endpoints."
            deployButtonText="DEPLOY RANGER"
        />
    );
};

export default ServiceView;
