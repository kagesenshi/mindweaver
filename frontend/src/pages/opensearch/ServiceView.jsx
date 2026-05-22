// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState, useEffect } from 'react';
import { Search, ExternalLink } from 'lucide-react';
import { useNotification } from '../../providers/NotificationProvider';
import PlatformServiceView from '../../components/PlatformServiceView';
import { InternalNetworkAccessBlock, CredentialBlock } from '../../components/ServiceBlocks';

const ServiceView = ({
    darkMode,
    selectedPlatformId,
    selectedPlatform,
    onBack,
    initialTab = 'connect',
    opensearch
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms } = opensearch;
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
                title: 'OpenSearch Internal HTTP Endpoint',
                code: `http://${selectedPlatform.name}.${platformState.extra_data.namespace}.svc.cluster.local:9200`,
                description: 'Internal network URI for accessing the OpenSearch REST API.'
            });
        }

        const uris = [];
        if (platformState?.opensearch_url) uris.push({ label: 'IPv4', uri: platformState.opensearch_url });
        if (platformState?.opensearch_url_ipv6) uris.push({ label: 'IPv6', uri: platformState.opensearch_url_ipv6 });

        return (
            <div className="space-y-6">
                {uris.length > 0 && (
                    <div className="mw-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold flex items-center gap-2">
                                <ExternalLink size={20} className="text-blue-500" />
                                Access OpenSearch API
                            </h3>
                        </div>
                        <p className="text-slate-500 dark:text-slate-400 mb-4 text-sm">
                            OpenSearch is available at the following external URIs:
                        </p>
                        <div className="space-y-4">
                            {uris.map((item, idx) => (
                                <div key={idx} className="flex flex-col gap-2">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{item.label}</span>
                                        <a 
                                            href={item.uri} 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center justify-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors w-max"
                                        >
                                            Open UI
                                            <ExternalLink size={14} />
                                        </a>
                                    </div>
                                    <div className="p-3 bg-slate-100 dark:bg-slate-800/50 rounded border border-slate-200 dark:border-slate-700">
                                         <span className="text-xs font-mono text-slate-600 dark:text-slate-400">{item.uri}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                {endpoints.length > 0 && (
                    <InternalNetworkAccessBlock
                        darkMode={darkMode}
                        icon={Search}
                        endpoints={endpoints}
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
            entityPath="/platform/opensearch"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Permanently delete all associated resources. This cannot be undone."
            notDeployedTitle="OpenSearch Not Deployed"
            notDeployedDescription="Deploy OpenSearch to see connection endpoints."
            deployButtonText="DEPLOY OPENSEARCH"
        />
    );
};

export default ServiceView;
//
