import React, { useEffect, useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
    Rocket,
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
            headerActions={
                <button
                    onClick={() => navigate('/platform/pgsql')}
                    className="mw-btn-primary px-4 py-2.5"
                >
                    <Rocket size={14} /> NEW DEPLOYMENT
                </button>
            }
            searchQuery={searchTerm}
            onSearchChange={(e) => setSearchTerm(e.target.value)}
            searchPlaceholder="Search within fleet..."
        >
            {loading ? (
                <div className="py-20 flex flex-col items-center justify-center space-y-4">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-slate-500 text-base font-medium">Scanning network for active resources...</p>
                </div>
            ) : filteredInstances.length === 0 ? (
                <div className="py-20 text-center border-2 border-dashed border-slate-800 rounded-[40px]">
                    <Server size={48} className="mx-auto text-slate-700 mb-4" />
                    <h3 className="text-lg font-bold text-slate-400">Quiet in the sector</h3>
                    <p className="text-slate-500 text-sm">No active resources found {selectedProject ? `for ${selectedProject.name}` : ''}.</p>
                </div>
            ) : (
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
            )}
        </PageLayout>
    );
};

export default HomePage;
