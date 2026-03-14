import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useHiveMetastore } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const HiveMetastorePage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const hms = useHiveMetastore();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = hms.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                hms={hms}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            hms={hms}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default HiveMetastorePage;
