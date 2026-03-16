import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { RefreshCcw } from 'lucide-react';
import { useStreamingSources } from '../../hooks/useResources';
import BaseSourceListingView from './BaseSourceListingView';

const StreamingSourcesPage = () => {
    const { darkMode } = useOutletContext();
    const hook = useStreamingSources();

    const renderSubtitle = (item) => (
        <div className="flex items-center gap-4 text-sm">
            <span className="mw-badge mw-badge-neutral">{item.broker_type?.toUpperCase()}</span>
            <span className="text-slate-300 dark:text-slate-600">|</span>
            <span className="truncate max-w-md">{item.bootstrap_servers}</span>
            {item.topic && (
                <>
                    <span className="text-slate-300 dark:text-slate-600">|</span>
                    <span>Topic: {item.topic}</span>
                </>
            )}
        </div>
    );

    return (
        <BaseSourceListingView
            darkMode={darkMode}
            hook={hook}
            title="Streaming Sources"
            description="Manage Kafka or Kinesis streams for real-time processing."
            entityPath="/streaming-sources"
            icon={RefreshCcw}
            renderSubtitle={renderSubtitle}
        />
    );
};

export default StreamingSourcesPage;
