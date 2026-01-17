import React, { useEffect, useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
    Server,
    Tag,
    Briefcase,
    Database
} from 'lucide-react';
import { usePgSql } from '../hooks/useResources';
import ResourceCard from '../components/ResourceCard';
import PageLayout from '../components/PageLayout';

const HomePage = () => {
    const { darkMode, selectedProject } = useOutletContext();
    const { platforms, loading } = usePgSql();
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');

    const filteredInstances = platforms.filter(inst => {
        const matchesProject = !selectedProject || inst.project_id === selectedProject.id;
        const matchesSearch = inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            String(inst.id).toLowerCase().includes(searchTerm.toLowerCase());
        return matchesProject && matchesSearch;
    });


    return (
        <PageLayout
            title={selectedProject ? `Stack: ${selectedProject.name}` : 'Unified Fleet'}
            description={`Monitoring ${filteredInstances.length} resources across all projects.`}
            searchQuery={searchTerm}
            onSearchChange={(e) => setSearchTerm(e.target.value)}
            searchPlaceholder="Search within fleet..."
            isLoading={loading}
            isEmpty={filteredInstances.length === 0}
            emptyState={{
                title: "Quiet in the sector",
                description: `No active resources found ${selectedProject ? `for ${selectedProject.name}` : ''}.`,
                icon: <Server size={48} className="text-slate-700" />
            }}
        >
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {filteredInstances.map(inst => (
                    <ResourceCard
                        key={inst.id}
                        icon={<Database size={20} />}
                        title={inst.name}
                        subtitle={inst.id}
                        status="running"
                        onClick={() => navigate('/platform/pgsql')}
                        footer={
                            <div className="flex items-center justify-between w-full">
                                <div className="flex items-center gap-2 text-slate-500">
                                    <Tag size={12} />
                                    <span className="text-sm font-bold">CloudNative PG</span>
                                </div>
                                <div className="flex items-center gap-2 text-blue-500/70">
                                    <Briefcase size={12} />
                                    <span className="text-sm font-bold uppercase truncate max-w-[80px]">
                                        {inst.project?.name || 'Service Component'}
                                    </span>
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
