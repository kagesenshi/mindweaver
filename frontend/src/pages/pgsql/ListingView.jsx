import React from 'react';
import { Database, Briefcase, Activity } from 'lucide-react';
import GenericListingView from '../../components/GenericListingView';
import { cn } from '../../utils/cn';

const ListingView = ({
    darkMode,
    selectedProject,
    pgsql,
    onSelectPlatform
}) => {
    const { platforms, loading, fetchPlatforms, getPlatformState, deletePlatform } = pgsql;

    const renderSubtitle = (platform, state) => (
        <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                <Briefcase size={14} />
                <span>Project: {platform.project_id}</span>
            </div>
            <div className={cn(
                "flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase border",
                state.status === 'online' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" :
                    state.status === 'error' ? "bg-rose-500/10 text-rose-500 border-rose-500/20" :
                        "bg-slate-500/10 text-slate-400 border-slate-500/20"
            )}>
                <div className={cn(
                    "w-1.5 h-1.5 rounded-full",
                    state.status === 'online' ? "bg-emerald-500" :
                        state.status === 'error' ? "bg-rose-500" :
                            "bg-slate-400"
                )} />
                {state.status || 'unknown'}
            </div>
            {state.active && (
                <div className="flex items-center gap-1 bg-blue-500/10 text-blue-500 border border-blue-500/20 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase">
                    <Activity size={10} />
                    Active
                </div>
            )}
        </div>
    );

    const renderBadges = (platform, state) => {
        return state.message ? [{ text: state.message, variant: "mw-badge-info" }] : [];
    };

    return (
        <GenericListingView
            title="PostgreSQL Clusters"
            description="High-availability PostgreSQL managed on Kubernetes"
            items={platforms}
            loading={loading}
            fetchItems={fetchPlatforms}
            deleteItem={deletePlatform}
            getItemState={getPlatformState}
            onSelectItem={(platform) => onSelectPlatform(platform.id, 'connect')}
            onEditItem={(platform) => onSelectPlatform(platform.id, 'configure')}
            icon={Database}
            entityPath="/platform/pgsql"
            createConfig={{
                title: "Provision PGSQL Cluster",
                buttonText: "NEW CLUSTER",
            }}
            searchPlaceholder="Search PostgreSQL clusters..."
            emptyState={{
                title: "No clusters found",
                description: selectedProject ? `No PostgreSQL clusters in ${selectedProject.name}.` : 'Create your first PostgreSQL cluster to get started.',
                icon: <Database size={48} className="text-slate-700" />
            }}
            renderSubtitle={renderSubtitle}
            renderBadges={renderBadges}
            deleteModalConfig={{
                title: "Delete PostgreSQL Cluster",
                message: "Are you sure you want to delete this PostgreSQL cluster? This will permanently remove all data and associated resources."
            }}
            darkMode={darkMode}
            selectedProject={selectedProject}
        />
    );
};

export default ListingView;
