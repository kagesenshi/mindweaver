/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useSSHKeys } from '../../hooks/useResources';
import ListingView from './ListingView';

const SSHKeysPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const sshKeysHook = useSSHKeys();

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            sshKeysHook={sshKeysHook}
        />
    );
};

export default SSHKeysPage;
