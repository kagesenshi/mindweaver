import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { Database } from 'lucide-react';
import { useDatabaseSources } from '../../hooks/useResources';
import BaseSourceListingView from './BaseSourceListingView';

const DatabaseSourcesPage = () => {
    const { darkMode } = useOutletContext();
    const hook = useDatabaseSources();

    const renderSubtitle = (item) => (
        <div className="flex items-center gap-4">
            <span>{item.engine || 'N/A'}</span>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <span>{item.host || 'N/A'}{item.port ? `:${item.port}` : ''}</span>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <span>{item.database || 'N/A'}</span>
        </div>
    );

    return (
        <BaseSourceListingView
            darkMode={darkMode}
            hook={hook}
            title="Database Sources"
            description="Manage external databases for Trino catalogs and Spark jobs."
            entityPath="/database-sources"
            icon={Database}
            renderSubtitle={renderSubtitle}
        />
    );
};

export default DatabaseSourcesPage;
