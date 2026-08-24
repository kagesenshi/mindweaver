/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useTrustedCerts } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const TrustedCertsPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const certsHook = useTrustedCerts();
    const [browsingCert, setBrowsingCert] = useState(null);

    if (browsingCert) {
        return (
            <ServiceView
                darkMode={darkMode}
                browsingCert={browsingCert}
                onBack={() => setBrowsingCert(null)}
                certsHook={certsHook}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            certsHook={certsHook}
            onSelectCert={setBrowsingCert}
        />
    );
};

export default TrustedCertsPage;
