/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
    Database,
    Server,
    Boxes,
    Wind,
    LayoutDashboard,
    Activity,
    ShieldCheck,
    Search,
    RefreshCcw,
    Network,
    TrendingUp,
    FolderKanban,
} from 'lucide-react';
import { usePgSql, useHiveMetastore, useTrino, useSuperset, useAirflow, useRanger, useSolr, useKafka, useNifi } from '../hooks/useResources';
import PageLayout from '../components/PageLayout';

const HomePage = () => {
    const { selectedProject, projects } = useOutletContext();
    const { platforms: pgsqlPlatforms, loading: pgsqlLoading } = usePgSql();
    const { platforms: hmsPlatforms, loading: hmsLoading } = useHiveMetastore();
    const { platforms: trinoPlatforms, loading: trinoLoading } = useTrino();
    const { platforms: supersetPlatforms, loading: supersetLoading } = useSuperset();
    const { platforms: airflowPlatforms, loading: airflowLoading } = useAirflow();
    const { platforms: rangerPlatforms, loading: rangerLoading } = useRanger();
    const { platforms: solrPlatforms, loading: solrLoading } = useSolr();
    const { platforms: kafkaPlatforms, loading: kafkaLoading } = useKafka();
    const { platforms: nifiPlatforms, loading: nifiLoading } = useNifi();
    const navigate = useNavigate();

    const loading = pgsqlLoading || hmsLoading || trinoLoading || supersetLoading || airflowLoading || rangerLoading || solrLoading || kafkaLoading || nifiLoading;

    const allInstances = [
        ...pgsqlPlatforms.map(p => ({ ...p, type: 'pgsql' })),
        ...hmsPlatforms.map(p => ({ ...p, type: 'hms' })),
        ...trinoPlatforms.map(p => ({ ...p, type: 'trino' })),
        ...supersetPlatforms.map(p => ({ ...p, type: 'superset' })),
        ...airflowPlatforms.map(p => ({ ...p, type: 'airflow' })),
        ...rangerPlatforms.map(p => ({ ...p, type: 'ranger' })),
        ...solrPlatforms.map(p => ({ ...p, type: 'solr' })),
        ...kafkaPlatforms.map(p => ({ ...p, type: 'kafka' })),
        ...nifiPlatforms.map(p => ({ ...p, type: 'nifi' }))
    ];

    // Filter instances based on selected project
    const projectInstances = allInstances.filter(inst => {
        return !selectedProject || inst.project_id === selectedProject.id;
    });

    // Count by service type within the project context
    const countsByType = projectInstances.reduce((acc, inst) => {
        acc[inst.type] = (acc[inst.type] || 0) + 1;
        return acc;
    }, {});

    const serviceTypes = [
        { key: 'pgsql', label: 'CloudNative PG', icon: Database, route: '/platform/pgsql', color: 'text-blue-500 bg-blue-500/10' },
        { key: 'hms', label: 'Hive Metastore', icon: Boxes, route: '/platform/hive-metastore', color: 'text-purple-500 bg-purple-500/10' },
        { key: 'kafka', label: 'Apache Kafka', icon: RefreshCcw, route: '/platform/kafka', color: 'text-amber-500 bg-amber-500/10' },
        { key: 'trino', label: 'Trino Cluster', icon: Wind, route: '/platform/trino', color: 'text-sky-500 bg-sky-500/10' },
        { key: 'airflow', label: 'Apache Airflow', icon: Activity, route: '/platform/airflow', color: 'text-teal-500 bg-teal-500/10' },
        { key: 'nifi', label: 'Apache NiFi', icon: Network, route: '/platform/nifi', color: 'text-orange-500 bg-orange-500/10' },
        { key: 'superset', label: 'Apache Superset', icon: LayoutDashboard, route: '/platform/superset', color: 'text-pink-500 bg-pink-500/10' },
        { key: 'ranger', label: 'Apache Ranger', icon: ShieldCheck, route: '/platform/ranger', color: 'text-emerald-500 bg-emerald-500/10' },
        { key: 'solr', label: 'Solr', icon: Search, route: '/platform/solr', color: 'text-yellow-500 bg-yellow-500/10' },
    ];

    // Calculate dynamic stats
    const totalResourcesCount = projectInstances.length;
    const activeProjectsCount = selectedProject ? 1 : projects?.length || 0;
    const dbClustersCount = countsByType['pgsql'] || 0;
    const dataStreamsCount = countsByType['kafka'] || 0;

    return (
        <PageLayout
            title={selectedProject ? `Stack: ${selectedProject.title}` : 'Unified Fleet'}
            description={`Monitoring ${totalResourcesCount} resources across all projects.`}
            isLoading={loading}
            isEmpty={projectInstances.length === 0}
            emptyState={{
                title: "Quiet in the sector",
                description: `No active resources found ${selectedProject ? `for ${selectedProject.title}` : ''}.`,
                icon: <Server size={48} className="text-slate-700" />
            }}
        >
            <div className="space-y-8">
                {/* Top-Level KPI Stats Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="mw-card p-6 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Total Deployments</p>
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-2">{totalResourcesCount}</h3>
                        </div>
                        <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-500">
                            <TrendingUp className="w-6 h-6" />
                        </div>
                    </div>

                    <div className="mw-card p-6 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Active Projects</p>
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-2">{activeProjectsCount}</h3>
                        </div>
                        <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-500">
                            <FolderKanban className="w-6 h-6" />
                        </div>
                    </div>

                    <div className="mw-card p-6 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Database Clusters</p>
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-2">{dbClustersCount}</h3>
                        </div>
                        <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                            <Database className="w-6 h-6" />
                        </div>
                    </div>

                    <div className="mw-card p-6 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Data Streams</p>
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-2">{dataStreamsCount}</h3>
                        </div>
                        <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500">
                            <RefreshCcw className="w-6 h-6" />
                        </div>
                    </div>
                </div>

                {/* Component Breakdown Section */}
                <div className="space-y-4">
                    <h3 className="text-xl font-bold tracking-tight text-slate-950 dark:text-white">Platform Breakdown</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {serviceTypes.map((st) => {
                            const count = countsByType[st.key] || 0;
                            const IconComponent = st.icon;
                            return (
                                <div
                                    key={st.key}
                                    onClick={() => navigate(st.route)}
                                    className="mw-card-interactive flex items-center justify-between p-5 border transition-all duration-200 border-slate-200 dark:border-slate-800"
                                >
                                    <div className="flex items-center gap-4 min-w-0">
                                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 ${st.color}`}>
                                            <IconComponent className="w-6 h-6" />
                                        </div>
                                        <div className="min-w-0">
                                            <h4 className="text-base font-bold truncate text-slate-900 dark:text-white leading-tight">
                                                {st.label}
                                            </h4>
                                            <span className="text-xs text-blue-500 font-medium mt-1 block">
                                                Manage &rarr;
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={`mw-badge ${count > 0 ? 'mw-badge-info' : 'mw-badge-neutral'}`}>
                                            {count}
                                        </span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </PageLayout>
    );
};

export default HomePage;
