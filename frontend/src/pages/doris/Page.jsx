/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useDoris } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const DorisPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const doris = useDoris();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = doris.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                doris={doris}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            doris={doris}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default DorisPage;
