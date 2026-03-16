import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { Globe } from 'lucide-react';
import { useWebSources } from '../../hooks/useResources';
import BaseSourceListingView from './BaseSourceListingView';

const WebSourcesPage = () => {
    const { darkMode } = useOutletContext();
    const hook = useWebSources();

    const renderSubtitle = (item) => (
        <div className="flex items-center gap-4 text-sm">
            <span className="truncate max-w-md">{item.url}</span>
        </div>
    );

    return (
        <BaseSourceListingView
            darkMode={darkMode}
            hook={hook}
            title="Web Sources"
            description="Manage websites for web scraping and data extraction."
            entityPath="/web-sources"
            icon={Globe}
            renderSubtitle={renderSubtitle}
        />
    );
};

export default WebSourcesPage;
