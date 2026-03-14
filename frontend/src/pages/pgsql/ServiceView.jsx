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
    pgsql
}) => {
    const { getPlatformState, refreshPlatformState, updatePlatformState, fetchPlatforms, fetchActions, executeAction } = pgsql;
    const [platformState, setPlatformState] = useState(null);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [availableActions, setAvailableActions] = useState([]);
    const [isExecutingAction, setIsExecutingAction] = useState(null);

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

    useEffect(() => {
        if (selectedPlatformId && platformState?.active) {
            fetchActions(selectedPlatformId).then(setAvailableActions);
        } else {
            setAvailableActions([]);
        }
    }, [selectedPlatformId, platformState?.active, fetchActions]);

    const handleRefresh = async () => {
        if (!selectedPlatformId) return;
        setIsRefreshing(true);
        try {
            const updated = await refreshPlatformState(selectedPlatformId);
            setPlatformState(updated);
        } finally {
            setIsRefreshing(false);
        }
    };

    const toggleActive = async () => {
        if (!selectedPlatformId || !platformState) return;
        setPlatformState({ ...platformState, active: true, status: 'pending', message: 'Triggering deployment...' });
        try {
            const response = await updatePlatformState(selectedPlatformId, { active: true });
            if (response) {
                setPlatformState(response);
            }
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
            if (response) {
                setPlatformState(response);
            }
            await handleRefresh();
        } catch (err) {
            showError(`Failed to decommission cluster: ${err.message}`);
            const original = await getPlatformState(selectedPlatformId);
            setPlatformState(original);
        }
    };

    const handleExecuteAction = async (actionName) => {
        if (!selectedPlatformId) return;
        setIsExecutingAction(actionName);
        try {
            await executeAction(selectedPlatformId, actionName);
            showSuccess(`Action ${actionName} triggered successfully`);
            await handleRefresh();
        } catch (err) {
            showError(`Failed to trigger action ${actionName}: ${err.message}`);
        } finally {
            setIsExecutingAction(null);
        }
    };

    const renderConnectTab = () => {
        const sortedPorts = platformState?.node_ports ? [...platformState.node_ports].sort((a, b) => {
            const getOrder = (name) => {
                if (name.endsWith('-rw-nodeport')) return 1;
                if (name.endsWith('-ro-nodeport')) return 2;
                if (name.endsWith('-r-nodeport')) return 3;
                return 4;
            };
            return getOrder(a.name) - getOrder(b.name);
        }) : [];

        return (
            <div className="space-y-6">
                {platformState?.extra_data?.namespace && (
                    <InternalNetworkAccessBlock 
                        darkMode={darkMode}
                        endpoints={[
                            { title: 'Read-Write', subtitle: 'Service Type', code: `${selectedPlatform.name}-rw.${platformState.extra_data.namespace}.svc.cluster.local:5432` },
                            { title: 'Read-Only', subtitle: 'Service Type', code: `${selectedPlatform.name}-ro.${platformState.extra_data.namespace}.svc.cluster.local:5432` },
                            { title: 'Read-Only (Any Nodes)', subtitle: 'Service Type', code: `${selectedPlatform.name}-r.${platformState.extra_data.namespace}.svc.cluster.local:5432` }
                        ]}
                    />
                )}

                {sortedPorts.length > 0 && (
                    <ExternalNetworkAccessBlock
                        darkMode={darkMode}
                        ports={sortedPorts.map(np => ({
                            label: np.name.endsWith('-rw-nodeport') ? 'Read-Write' :
                                   np.name.endsWith('-ro-nodeport') ? 'Read-Only' :
                                   np.name.endsWith('-r-nodeport') ? 'Read-Only (Any Nodes)' : 'PostgreSQL',
                            node_port: np.node_port
                        }))}
                        clusterNodes={platformState.cluster_nodes}
                        cliInfo={{
                            command: `psql "host=${platformState.cluster_nodes?.[0]?.ipv4 || '[NODE_IP]'} port=${sortedPorts?.[0]?.node_port || '[PORT]'} user=${platformState?.db_user || 'pending'} dbname=${platformState?.db_name || 'pending'} sslmode=verify-full sslrootcert=ca.crt"`,
                            languageButtons: ['python']
                        }}
                    />
                )}

                {platformState?.db_user && platformState?.db_pass && (
                    <CredentialBlock
                        darkMode={darkMode}
                        credentials={[
                            { label: 'Username', value: platformState?.db_user },
                            { label: 'Password', value: platformState?.db_pass, isMasked: true },
                            { label: 'Database', value: platformState?.db_name }
                        ]}
                        caCert={platformState?.db_ca_crt}
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
            availableActions={availableActions}
            isExecutingAction={isExecutingAction}
            onExecuteAction={handleExecuteAction}
            icon={Database}
            iconClassName="text-blue-400"
            entityPath="/platform/pgsql"
            fetchPlatforms={fetchPlatforms}
            renderConnectTab={renderConnectTab}
            decommissionWarningText="Decommissioning this cluster will permanently delete all associated Kubernetes resources and database data. This action cannot be undone."
            notDeployedTitle="Cluster Not Deployed"
            notDeployedDescription="This PostgreSQL cluster is currently not deployed. Deploy the cluster to see connection details and access endpoints."
            deployButtonText="DEPLOY CLUSTER"
        />
    );
};

export default ServiceView;
