// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, ExternalNetworkAccessBlock, CredentialBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    solr
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = solr;
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
            const svcName = platformState.extra_data.service_name || `${selectedPlatform.name}-solrcloud-common`;
            endpoints.push({
                title: 'Solr Internal HTTPS Endpoint',
                code: `https://${svcName}.${platformState.extra_data.namespace}.svc.cluster.local:8983`,
                description: 'Internal network URI for accessing the Solr Admin API.'
            });
        }

        let solrUrlObj = null;
        if (platformState?.solr_url) {
            try {
                solrUrlObj = new URL(platformState.solr_url);
            } catch (e) {
                console.error("Failed to parse solr_url:", e);
            }
        }

        const ports = [];
        let isIngressUsed = false;
        const ingressDomain = platformState?.extra_data?.ingress_domain;

        if (solrUrlObj && ingressDomain && solrUrlObj.hostname.endsWith(ingressDomain)) {
            ports.push({
                label: 'Solr API (Envoy Ingress)',
                load_balancer_ips: [solrUrlObj.hostname],
                port: solrUrlObj.port ? parseInt(solrUrlObj.port) : (solrUrlObj.protocol === 'https:' ? 443 : 80),
                scheme: solrUrlObj.protocol.replace(':', '')
            });
            isIngressUsed = true;
        }

        const httpPort = platformState?.node_ports?.find(np => np.port === 8983);
        if (httpPort) {
            ports.push({
                label: 'Solr API (NodePort)',
                node_port: httpPort.node_port,
                scheme: solrUrlObj ? solrUrlObj.protocol.replace(':', '') : 'https'
            });
        } else if (!isIngressUsed && solrUrlObj) {
            ports.push({
                label: 'Solr API (NodePort)',
                node_port: solrUrlObj.port ? parseInt(solrUrlObj.port) : 8983,
                scheme: solrUrlObj.protocol.replace(':', '')
            });
        }

        return (
            <div className="space-y-6">
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={Search}
                        endpoints={endpoints}
                    />
                )}
                {ports.length > 0 && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={ports}
                        clusterNodes={platformState.cluster_nodes}
                        icon={Search}
                        iconColorClass="text-blue-400"
                    />
                )}
                {platformState?.admin_password && (
                    <CredentialBlock
                        darkMode={darkMode}
                        credentials={[
                            { label: 'Admin Username', value: 'admin', isMasked: false },
                            { label: 'Admin Password', value: platformState?.admin_password, isMasked: true }
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
            icon={Search}
            iconClassName="text-blue-400"
            entityPath="/platform/solr"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. This cannot be undone."
            notDeployedTitle="Solr Not Deployed"
            notDeployedDescription="Deploy Solr to see connection endpoints."
            deployButtonText="DEPLOY SOLR"
        />
    );
};

export default ServiceView;
