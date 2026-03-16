import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';
import { useApiSources } from '../../hooks/useResources';
import BaseSourceListingView from './BaseSourceListingView';

const ApiSourcesPage = () => {
    const { darkMode } = useOutletContext();
    const hook = useApiSources();

    const renderSubtitle = (item) => (
        <div className="flex items-center gap-4 text-sm">
            <span className="mw-badge mw-badge-neutral">{item.api_type?.toUpperCase()}</span>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <span className="truncate max-w-md">{item.base_url}</span>
        </div>
    );

    return (
        <BaseSourceListingView
            darkMode={darkMode}
            hook={hook}
            title="API Sources"
            description="Connect to REST, GraphQL, or SOAP APIs for automated ingestion."
            entityPath="/api-sources"
            icon={ExternalLink}
            renderSubtitle={renderSubtitle}
        />
    );
};

export default ApiSourcesPage;
