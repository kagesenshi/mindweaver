import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useLdapConfigs } from '../../hooks/useResources';
import ListingView from './ListingView';

const LdapConfigPage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const ldapConfigsHook = useLdapConfigs();

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            ldapConfigsHook={ldapConfigsHook}
        />
    );
};

export default LdapConfigPage;
