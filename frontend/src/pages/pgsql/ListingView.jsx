import React, { useState, useEffect } from 'react';
import { Trash2, Database, Search, Edit2, ChevronRight, Activity, CheckCircle2, XCircle, Briefcase } from 'lucide-react';
import PageLayout from '../../components/PageLayout';
import ListingItem from '../../components/ListingItem';
import { cn } from '../../utils/cn';

const ListingView = ({
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
            <div className="grid grid-cols-1 gap-4">
                {filteredPlatforms.map(platform => {
                    const state = allPlatformStates[platform.id] || {};
                    const statusMessage = state.message;

                    return (
                        <ListingItem
                            key={platform.id}
                            icon={Database}
                            title={platform.title}
                            badges={statusMessage ? [{ text: statusMessage, variant: "mw-badge-info" }] : []}
                            subtitle={
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
                            }
                            onClick={() => onSelectPlatform(platform.id, 'connect')}
                            actions={
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onSelectPlatform(platform.id, 'configure');
                                        }}
                                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                                        title="Configure PostgreSQL Cluster"
                                    >
                                        <Edit2 size={18} />
                                    </button>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDelete(platform.id, platform.name);
                                        }}
                                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                                        title="Delete PGSQL Cluster"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                    <div className="w-px h-8 bg-slate-200 dark:bg-slate-800 mx-2" />
                                    <ChevronRight size={20} className="text-slate-300 dark:text-slate-600" />
                                </div>
                            }
                        />
                    );
                })}
            </div>
        </PageLayout>
    );
};

export default ListingView;
