import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useK8sClusters } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const K8sClustersPage = () => {
    const context = useOutletContext();
    const clustersHook = useK8sClusters();
    const [selectedClusterId, setSelectedClusterId] = useState(null);

    const handleSelectCluster = (id) => {
        setSelectedClusterId(id);
    };

    const selectedCluster = clustersHook.clusters.find(p => p.id === selectedClusterId);

    if (selectedCluster) {
        return (
            <ServiceView
                context={context}
                selectedClusterId={selectedClusterId}
                selectedCluster={selectedCluster}
                onBack={() => setSelectedClusterId(null)}
                clustersHook={clustersHook}
            />
        );
    }

    return (
        <ListingView
            context={context}
            clustersHook={clustersHook}
            onSelectCluster={handleSelectCluster}
        />
    );
};

export default K8sClustersPage;
