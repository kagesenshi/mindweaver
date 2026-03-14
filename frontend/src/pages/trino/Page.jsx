import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useTrino } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const TrinoPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const trino = useTrino();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = trino.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default TrinoPage;
