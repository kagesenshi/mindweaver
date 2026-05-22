// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useOpenSearch } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const OpenSearchPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const opensearch = useOpenSearch();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = opensearch.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                opensearch={opensearch}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            opensearch={opensearch}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default OpenSearchPage;
