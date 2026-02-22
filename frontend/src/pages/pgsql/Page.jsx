import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { usePgSql } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const PgSqlPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const pgsql = usePgSql();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = pgsql.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                pgsql={pgsql}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            pgsql={pgsql}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default PgSqlPage;
