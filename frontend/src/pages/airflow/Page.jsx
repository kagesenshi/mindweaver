import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useAirflow } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const AirflowPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const airflow = useAirflow();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = airflow.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                airflow={airflow}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            airflow={airflow}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default AirflowPage;
