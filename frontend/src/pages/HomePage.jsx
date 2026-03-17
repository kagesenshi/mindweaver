import React, { useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
    Briefcase,
    Database,
    ChevronRight,
    Server,
    Boxes,
    Wind,
    LayoutDashboard
} from 'lucide-react';
import { usePgSql, useHiveMetastore, useTrino, useSuperset } from '../hooks/useResources';
import PageLayout from '../components/PageLayout';
import ListingItem from '../components/ListingItem';

const HomePage = () => {
    const { selectedProject } = useOutletContext();
    const { platforms: pgsqlPlatforms, loading: pgsqlLoading } = usePgSql();
    const { platforms: hmsPlatforms, loading: hmsLoading } = useHiveMetastore();
    const { platforms: trinoPlatforms, loading: trinoLoading } = useTrino();
    const { platforms: supersetPlatforms, loading: supersetLoading } = useSuperset();
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');

    const loading = pgsqlLoading || hmsLoading || trinoLoading || supersetLoading;

    const allInstances = [
        ...pgsqlPlatforms.map(p => ({ ...p, type: 'pgsql' })),
        ...hmsPlatforms.map(p => ({ ...p, type: 'hms' })),
        ...trinoPlatforms.map(p => ({ ...p, type: 'trino' })),
        ...supersetPlatforms.map(p => ({ ...p, type: 'superset' }))
    ];

    const filteredInstances = allInstances.filter(inst => {
        const matchesProject = !selectedProject || inst.project_id === selectedProject.id;
        const nameMatch = (inst.title || inst.name || '').toLowerCase().includes(searchTerm.toLowerCase());
        const idMatch = String(inst.id || '').toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && (nameMatch || idMatch);
    });


    return (
        <PageLayout
            title={selectedProject ? `Stack: ${selectedProject.title}` : 'Unified Fleet'}
            description={`Monitoring ${filteredInstances.length} resources across all projects.`}
            searchQuery={searchTerm}
            onSearchChange={(e) => setSearchTerm(e.target.value)}
            searchPlaceholder="Search within fleet..."
            isLoading={loading}
            isEmpty={filteredInstances.length === 0}
            emptyState={{
                title: "Quiet in the sector",
                description: `No active resources found ${selectedProject ? `for ${selectedProject.title}` : ''}.`,
                icon: <Server size={48} className="text-slate-700" />
            }}
        >
            <div className="grid grid-cols-1 gap-4">
                {filteredInstances.map(inst => (
                    <ListingItem
                        key={`${inst.type}-${inst.id}`}
                        icon={inst.type === 'hms' ? Boxes : inst.type === 'trino' ? Wind : inst.type === 'superset' ? LayoutDashboard : Database}
                        title={inst.title || inst.name}
                        badges={[{ 
                            text: inst.type === 'hms' ? "Hive Metastore" : inst.type === 'trino' ? "Trino Cluster" : inst.type === 'superset' ? "Apache Superset" : "CloudNative PG", 
                            variant: "mw-badge-neutral" 
                        }]}
                        subtitle={inst.id}
                        onClick={() => {
                            if (inst.type === 'hms') navigate('/platform/hive-metastore');
                            else if (inst.type === 'trino') navigate('/platform/trino');
                            else if (inst.type === 'superset') navigate('/platform/superset');
                            else navigate('/platform/pgsql');
                        }}
                        actions={
                            <div className="flex items-center gap-12">
                                <div className="flex items-center gap-2 text-blue-500/70">
                                    <Briefcase size={16} />
                                    <span className="text-base font-bold uppercase truncate max-w-[150px]">
                                        {inst.project?.title || 'Service Component'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <ChevronRight className="w-5 h-5 text-slate-300 dark:text-slate-600" />
                                </div>
                            </div>
                        }
                    />
                ))}
            </div>
        </PageLayout>
    );
};

export default HomePage;
