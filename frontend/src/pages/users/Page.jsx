/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useUsers } from '../../hooks/useResources';
import ListingView from './ListingView';

const UsersPage = () => {
    const { darkMode } = useOutletContext();
    const usersHook = useUsers();

    return (
        <ListingView
            darkMode={darkMode}
            usersHook={usersHook}
        />
    );
};

export default UsersPage;
