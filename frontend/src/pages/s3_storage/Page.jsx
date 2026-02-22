import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useS3Storages } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const S3StoragePage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const s3Storages = useS3Storages();
    const [browsingStorage, setBrowsingStorage] = useState(null);

    const handleSelectStorage = (storage) => {
        setBrowsingStorage(storage);
    };

    if (browsingStorage) {
        return (
            <ServiceView
                darkMode={darkMode}
                browsingStorage={browsingStorage}
                onBack={() => setBrowsingStorage(null)}
                s3Storages={s3Storages}
            />
        );
    }

    return (
        <ListingView
            darkMode={darkMode}
            selectedProject={selectedProject}
            s3Storages={s3Storages}
            onSelectStorage={handleSelectStorage}
        />
    );
};

export default S3StoragePage;
