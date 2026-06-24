// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useNifi } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

/**
 * NiFiPage is the main container page component for Apache NiFi platform service in the frontend.
 * It manages state for the selected NiFi platform instance and toggles between the listing and service views.
 */
const NiFiPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const nifi = useNifi();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = nifi.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                nifi={nifi}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            nifi={nifi}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default NiFiPage;
