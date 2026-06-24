// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState, useEffect } from 'react';
import { Network, ExternalLink } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalAccessBlock } from '../../components/ServiceBlocks';

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
        const externalLinks = [];

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

        // Web UI access if nifi_uri is present
        if (platformState?.nifi_uri) {
            externalLinks.push({
                label: 'NiFi Web UI',
                url: platformState.nifi_uri,
                description: 'Direct link to Apache NiFi Web Console.'
            });
        }

        return (
            <div className="space-y-6">
                {externalLinks.length > 0 && (
                    <ExternalAccessBlock
                        darkMode={darkMode}
                        links={externalLinks}
                        icon={ExternalLink}
                    />
                )}
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={Network}
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
