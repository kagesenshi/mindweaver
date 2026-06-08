// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useSolr } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const SolrPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const solr = useSolr();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = solr.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                solr={solr}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            solr={solr}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default SolrPage;
