// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Layers, Box, Info, Tag, RefreshCcw } from 'lucide-react';
import { useStacks } from '../../hooks/useResources';
import { cn } from '../../utils/cn';

// Mapping backend component keys to user-friendly titles
const COMPONENT_TITLES = {
    pgsql: 'PostgreSQL',
    nifi: 'Apache NiFi',
    airflow: 'Apache Airflow',
    kafka: 'Apache Kafka',
    ranger: 'Apache Ranger',
    superset: 'Apache Superset',
    hive_metastore: 'Hive Metastore',
    trino: 'Trino',
    argocd: 'ArgoCD',
    'cert-manager': 'Cert Manager',
    cnpg: 'CloudNativePG Operator',
    'envoy-gateway': 'Envoy Gateway',
    'kafka-operator': 'Strimzi Kafka Operator',
    'nifikop-operator': 'NiFiKop Operator',
};

const StacksPage = () => {
    const { darkMode } = useOutletContext();
    const { stacks, loading, error } = useStacks();
    const [selectedStackId, setSelectedStackId] = useState(null);

    const cardBg = darkMode ? "bg-slate-900/60 border-slate-800" : "bg-white border-slate-200";
    const titleColor = darkMode ? "text-white" : "text-slate-900";
    const descColor = darkMode ? "text-slate-400" : "text-slate-600";
    const subBg = darkMode ? "bg-slate-950/60" : "bg-slate-50";

    const selectedStack = stacks.find(s => s.id === selectedStackId) || stacks[0];

    if (loading && stacks.length === 0) {
        return (
            <div className="p-12 flex flex-col items-center justify-center space-y-4">
                <RefreshCcw className="animate-spin text-blue-500" size={32} />
                <p className="text-slate-500 text-base font-medium">Loading available stacks...</p>
            </div>
        );
    }

    return (
        <div className="p-6 md:p-8 space-y-8 w-full">
            {/* Header */}
            <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-blue-600/10 rounded-2xl flex items-center justify-center border border-blue-500/20">
                        <Layers className="text-blue-500" size={24} />
                    </div>
                    <div>
                        <h1 className={cn("text-3xl font-bold tracking-tight", titleColor)}>Stack Registry</h1>
                        <p className={descColor}>Pre-configured, certified version combinations for platform components.</p>
                    </div>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3 text-rose-500">
                    <Info size={20} />
                    <span>Failed to load stacks: {error.message || 'Unknown error'}</span>
                </div>
            )}

            {stacks.length === 0 ? (
                <div className={cn("p-12 text-center rounded-3xl border border-dashed", cardBg)}>
                    <Layers size={48} className="mx-auto text-slate-500 mb-4" />
                    <h3 className={cn("text-lg font-bold mb-2", titleColor)}>No stacks found</h3>
                    <p className={descColor}>There are no certified stacks loaded. Run stack import command in CLI to initialize defaults.</p>
                </div>
            ) : (
            <div className="flex flex-col lg:flex-row gap-8 items-start">
                    {/* Stacks Sidebar */}
                    <div className="space-y-4 w-full lg:w-80 shrink-0">
                        <h2 className={cn("text-sm font-bold uppercase tracking-wider px-1", descColor)}>Available Stacks</h2>
                        <div className="space-y-3">
                            {stacks.map((stack) => {
                                const isSelected = selectedStack?.id === stack.id;
                                return (
                                    <div
                                        key={stack.id}
                                        onClick={() => setSelectedStackId(stack.id)}
                                        className={cn(
                                            "p-5 rounded-2xl border transition-all duration-200 cursor-pointer shadow-sm relative overflow-hidden group",
                                            isSelected 
                                                ? "bg-blue-600/10 border-blue-500/30 text-blue-500" 
                                                : cn("hover:border-blue-500/20 hover:bg-slate-50/50 dark:hover:bg-slate-800/30", cardBg)
                                        )}
                                    >
                                        <div className="flex justify-between items-start mb-1">
                                            <h3 className={cn("font-bold text-lg", isSelected ? "text-blue-500" : titleColor)}>
                                                {stack.title || stack.name}
                                            </h3>
                                            <span className={cn(
                                                "text-xs px-2.5 py-1 rounded-full font-semibold border",
                                                isSelected 
                                                    ? "bg-blue-500/20 border-blue-500/30 text-blue-400"
                                                    : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400"
                                            )}>
                                                {stack.version}
                                            </span>
                                        </div>
                                        <p className={cn("text-sm mb-2", descColor)}>Identifier: {stack.name}</p>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Stack Details Pane */}
                    {selectedStack && (
                        <div className={cn("flex-1 w-full border rounded-3xl p-6 md:p-8 shadow-sm space-y-6", cardBg)}>
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <h2 className={cn("text-2xl font-bold", titleColor)}>
                                        {selectedStack.title || selectedStack.name} Details
                                    </h2>
                                </div>
                                <p className={descColor}>
                                    Below are the locked component versions and image repository specifications certified under stack version <strong className={titleColor}>{selectedStack.version}</strong>.
                                </p>
                            </div>

                            {/* Components Grid */}
                            <div className="space-y-4">
                                {Object.entries(selectedStack.configuration?.components || {}).map(([key, comp]) => {
                                    const mainImage = comp.images?.main || {};
                                    return (
                                        <div
                                            key={key}
                                            className={cn(
                                                "p-5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 border transition-all hover:shadow-md",
                                                subBg,
                                                darkMode ? "border-slate-800/80" : "border-slate-200"
                                            )}
                                        >
                                            <div className="flex items-center gap-3 shrink-0">
                                                <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center shrink-0 border border-blue-500/20">
                                                    <Box className="text-blue-500" size={20} />
                                                </div>
                                                <div>
                                                    <h4 className={cn("font-bold text-base", titleColor)}>
                                                        {COMPONENT_TITLES[key] || key}
                                                    </h4>
                                                    <p className={cn("text-xs font-medium uppercase tracking-wider", descColor)}>
                                                        {key}
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="flex flex-col md:flex-row md:items-center gap-4 w-full md:justify-end">
                                                <div className="flex flex-col shrink-0 min-w-0 md:text-right">
                                                    <span className={cn("text-xs font-semibold uppercase tracking-wider mb-0.5", descColor)}>
                                                        Image Repository
                                                    </span>
                                                    <span className={cn("text-sm font-mono break-all", titleColor)} title={mainImage.image}>
                                                        {mainImage.image || 'N/A'}
                                                    </span>
                                                </div>

                                                <div className="flex flex-col shrink-0 md:text-right md:w-28">
                                                    <span className={cn("text-xs font-semibold uppercase tracking-wider mb-0.5", descColor)}>
                                                        Locked Tag
                                                    </span>
                                                    <div className="flex items-center gap-1.5 md:justify-end">
                                                        <Tag size={12} className="text-blue-500 shrink-0" />
                                                        <span className={cn("text-sm font-semibold font-mono", titleColor)}>
                                                            {mainImage.tag || 'N/A'}
                                                        </span>
                                                    </div>
                                                </div>

                                                {comp.chart_version && (
                                                    <div className="flex flex-col shrink-0 md:text-right md:w-32">
                                                        <span className={cn("text-xs font-semibold uppercase tracking-wider mb-0.5", descColor)}>
                                                            Chart Version
                                                        </span>
                                                        <span className={cn("text-sm font-semibold font-mono", titleColor)}>
                                                            {comp.chart_version}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default StacksPage;
