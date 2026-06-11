/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useContainerRegistries } from '../../hooks/useResources';
import ListingView from './ListingView';

const ContainerRegistriesPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const registriesHook = useContainerRegistries();

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            registriesHook={registriesHook}
        />
    );
};

export default ContainerRegistriesPage;
