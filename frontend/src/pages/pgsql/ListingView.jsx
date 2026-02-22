import React, { useState, useEffect } from 'react';
import { Database, Server, Activity, Loader2 } from 'lucide-react';
import ResourceCard from '../../components/ResourceCard';
import PageLayout from '../../components/PageLayout';

const ListingView = ({
    darkMode,
    selectedProject,
    pgsql,
    onSelectPlatform
}) => {
    const { platforms, loading, fetchPlatforms, getPlatformState, deletePlatform } = pgsql;
    const [searchTerm, setSearchTerm] = useState('');
    const [allPlatformStates, setAllPlatformStates] = useState({});

    const filteredPlatforms = platforms.filter(p => {
        const matchesProject = !selectedProject || p.project_id === selectedProject.id;
        const matchesSearch = (p.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (p.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            String(p.id).toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && matchesSearch;
    });

    useEffect(() => {
        let timer;
        const fetchStates = async () => {
            if (platforms.length === 0) return;
            const states = {};
            await Promise.all(platforms.map(async (p) => {
                try {
                    const state = await getPlatformState(p.id);
                    states[p.id] = state;
                } catch (e) {
                    console.error(`Failed to fetch state for platform ${p.id}`, e);
                }
            }));
            setAllPlatformStates(states);
        };

        if (platforms.length > 0) {
            fetchStates();
            timer = setInterval(fetchStates, 5000);
        }

        return () => {
            if (timer) clearInterval(timer);
        };
    }, [platforms, getPlatformState]);

    const handleDelete = async (id, confirmName) => {
        await deletePlatform(id, confirmName);
    };

    return (
        <PageLayout
            title="PostgreSQL Clusters"
            description="High-availability PostgreSQL managed on Kubernetes"
            createConfig={{
                title: "Provision PGSQL Cluster",
                entityPath: "/platform/pgsql",
                buttonText: "NEW CLUSTER",
                initialData: { project_id: selectedProject?.id },
                onSuccess: async () => {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    await fetchPlatforms();
                }
            }}
            searchQuery={searchTerm}
            onSearchChange={(e) => setSearchTerm(e.target.value)}
            searchPlaceholder="Search PostgreSQL clusters..."
            isLoading={loading}
            isEmpty={filteredPlatforms.length === 0}
            emptyState={{
                title: "No clusters found",
                description: selectedProject ? `No PostgreSQL clusters in ${selectedProject.name}.` : 'Create your first PostgreSQL cluster to get started.',
                icon: <Database size={48} className="text-slate-700" />
            }}
        >
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {filteredPlatforms.map(platform => (
                    <ResourceCard
                        key={platform.id}
                        onClick={() => {
                            onSelectPlatform(platform.id, 'connect');
                        }}
                        icon={<Server size={20} />}
                        title={platform.title}
                        subtitle={platform.id}
                        status={allPlatformStates[platform.id]?.status || (allPlatformStates[platform.id]?.active ? 'active' : 'stopped')}
                        onEdit={() => {
                            onSelectPlatform(platform.id, 'configure');
                        }}
                        resourceName={platform.name}
                        darkMode={darkMode}
                        onDelete={(name) => handleDelete(platform.id, name)}
                        footer={allPlatformStates[platform.id]?.message && (
                            <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 dark:bg-slate-800/50 px-2 py-1 rounded-lg truncate">
                                {allPlatformStates[platform.id]?.status === 'pending' ? (
                                    <Loader2 size={12} className="text-blue-500 shrink-0 animate-spin" />
                                ) : (
                                    <Activity size={12} className="text-blue-500 shrink-0" />
                                )}
                                <span className="truncate">{allPlatformStates[platform.id].message}</span>
                            </div>
                        )}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-slate-500">
                                <Activity size={12} />
                                <span className="text-base font-bold">{platform.instances} Instances</span>
                            </div>
                            <div className="flex items-center gap-2 text-blue-500/70">
                                <Database size={12} />
                                <span className="text-base font-bold uppercase truncate max-w-[120px]">{platform.image}</span>
                            </div>
                        </div>
                    </ResourceCard>
                ))}
            </div>
        </PageLayout>
    );
};

export default ListingView;
