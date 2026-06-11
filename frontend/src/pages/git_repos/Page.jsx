/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useGitRepos } from '../../hooks/useResources';
import ListingView from './ListingView';

const GitReposPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const gitReposHook = useGitRepos();

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            gitReposHook={gitReposHook}
        />
    );
};

export default GitReposPage;
