import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { useDataSources } from '../../hooks/useResources';
import ListingView from './ListingView';

const DataSourcesPage = () => {
    const { darkMode } = useOutletContext();
    const dataSourcesHook = useDataSources();

    return (
        <ListingView
            darkMode={darkMode}
            dataSourcesHook={dataSourcesHook}
        />
    );
};

export default DataSourcesPage;
