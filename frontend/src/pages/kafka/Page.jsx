// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useKafka } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const KafkaPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const kafka = useKafka();
    const [selectedPlatformId, setSelectedPlatformId] = useState(null);
    const [initialTab, setInitialTab] = useState('connect');

    const handleSelectPlatform = (id, tab = 'connect') => {
        setSelectedPlatformId(id);
        setInitialTab(tab);
    };

    const selectedPlatform = kafka.platforms.find(p => p.id === selectedPlatformId);

    if (selectedPlatform) {
        return (
            <ServiceView
                darkMode={darkMode}
                selectedPlatformId={selectedPlatformId}
                selectedPlatform={selectedPlatform}
                onBack={() => setSelectedPlatformId(null)}
                initialTab={initialTab}
                kafka={kafka}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            kafka={kafka}
            onSelectPlatform={handleSelectPlatform}
        />
    );
};

export default KafkaPage;
