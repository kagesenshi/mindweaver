import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useSuperset } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const SupersetPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const superset = useSuperset();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = superset.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                superset={superset}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            superset={superset}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default SupersetPage;
