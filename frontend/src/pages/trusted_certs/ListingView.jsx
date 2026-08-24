/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React from 'react';
import { ShieldCheck } from 'lucide-react';
import GenericListingView from '../../components/GenericListingView';

const ListingView = ({
    darkMode,
    selectedProject,
    certsHook,
    onSelectCert
}) => {
    const { certs, loading, deleteCert, fetchCerts } = certsHook;

    const renderSubtitle = (cert) => {
        const preview = cert.certificate ? cert.certificate.slice(0, 60) + '...' : '';
        return (
            <span className="text-slate-400 dark:text-slate-500 font-mono text-xs block truncate mt-1">
                {preview}
            </span>
        );
    };

    return (
        <GenericListingView
            title="Trusted Certificates"
            description="Import external CA and trusted certificates. Deployed platform services will automatically import them into JVM truststores."
            items={certs}
            loading={loading}
            fetchItems={fetchCerts}
            deleteItem={deleteCert}
            onSelectItem={onSelectCert}
            onEditItem={onSelectCert}
            icon={ShieldCheck}
            entityPath="/trusted_certs"
            createConfig={{
                title: "Import Trusted Certificate",
                buttonText: "IMPORT CERTIFICATE",
                initialData: {},
                onSuccess: () => {},
            }}
            searchPlaceholder="Search certificates..."
            emptyState={{
                title: "No Trusted Certificates found",
                description: selectedProject
                    ? `No trusted certificates configured in ${selectedProject.name}.`
                    : 'Import your first trusted certificate to get started.',
                icon: <ShieldCheck size={48} className="text-slate-700" />
            }}
            renderSubtitle={renderSubtitle}
            deleteModalConfig={{
                title: "Delete Trusted Certificate",
                message: "Are you sure you want to delete this trusted certificate? Deployed services might fail to communicate with external resources requiring this CA."
            }}
            darkMode={darkMode}
            selectedProject={selectedProject}
            searchFields={["name", "title"]}
        />
    );
};

export default ListingView;
