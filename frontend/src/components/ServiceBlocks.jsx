// SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
// SPDX-License-Identifier: AGPLv3+

import React, { useState } from 'react';
import { Server, Lock, Eye, EyeOff, Copy, AlertCircle, ExternalLink } from 'lucide-react';
import { cn } from '../utils/cn';

export const ServiceBlock = ({ darkMode, icon, iconColorClass = "text-emerald-500", iconBgClass = "bg-emerald-500/10", title, children }) => {
    const IconComponent = icon;
    return (
        <div className="mw-panel">
            <div className={cn("p-4 border-b flex items-center justify-between", darkMode ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-slate-50')}>
                <div className="flex items-center gap-3">
                    <div className={cn("p-2 rounded-lg", iconBgClass, iconColorClass)}><IconComponent size={18} /></div>
                    <h4 className="text-base font-bold tracking-wider leading-none text-slate-900 dark:text-white">{title}</h4>
                </div>
            </div>
            <div className="p-6">
                {children}
            </div>
        </div>
    );
};

export const EndpointCard = ({ title, subtitle, code, description, copyValue, codeClassName = "text-emerald-600 dark:text-emerald-400" }) => (
    <div className="p-5 border rounded-2xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 flex flex-col group/item relative h-full">
        <div className="flex items-center justify-between mb-2">
            <div>
                {subtitle && <p className="text-xs text-slate-500 font-bold uppercase tracking-widest leading-none mb-1">{subtitle}</p>}
                <h5 className="text-lg font-bold text-slate-900 dark:text-white leading-none">{title}</h5>
            </div>
        </div>
        <div className="mt-2 p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <code className={cn("text-xs font-mono truncate px-1", codeClassName)}>
                {code}
            </code>
            <button
                onClick={() => navigator.clipboard.writeText(copyValue || code)}
                className="p-1 text-slate-400 hover:text-emerald-500 transition-colors shrink-0"
                title="Copy endpoint"
            >
                <Copy size={14} />
            </button>
        </div>
        {description && (
            <p className="mt-4 text-xs text-slate-500 leading-relaxed">{description}</p>
        )}
    </div>
);

export const InternalNetworkAccessBlock = ({ darkMode, endpoints, icon = Server, iconColorClass = "text-emerald-500", iconBgClass = "bg-emerald-500/10" }) => (
    <ServiceBlock darkMode={darkMode} icon={icon} iconColorClass={iconColorClass} iconBgClass={iconBgClass} title="Internal Network Access">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {endpoints.map((eps, i) => (
                <div key={i}>
                    <EndpointCard 
                        title={eps.title} 
                        subtitle={eps.subtitle}
                        code={eps.code} 
                        description={eps.description} 
                        copyValue={eps.copyValue} 
                        codeClassName={eps.codeClassName}
                    />
                </div>
            ))}
        </div>
    </ServiceBlock>
);

export const ExternalNetworkAccessBlock = ({ 
    darkMode, 
    ports, 
    clusterNodes, 
    cliInfo, 
    guideTitle = "External Connection Guide", 
    guideText = "Use any of the <strong>Node IP:Port</strong> combinations listed above to connect from outside the cluster.",
    cliLanguage = "bash",
    cliTitle = "CLI Example",
    icon = Server,
    iconColorClass = "text-indigo-500",
    iconBgClass = "bg-indigo-500/10"
}) => {
    return (
        <ServiceBlock darkMode={darkMode} icon={icon} iconColorClass={iconColorClass} iconBgClass={iconBgClass} title="External Network Access">
            <div className="space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {ports.map((np, i) => {
                        const isLoadBalancer = np.load_balancer_ips !== undefined;
                        return (
                            <div key={i} className="p-5 border rounded-2xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 flex flex-col h-full">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <p className="text-xs text-slate-500 font-bold uppercase tracking-widest leading-none mb-1">Service Type</p>
                                        <h5 className="text-lg font-bold text-slate-900 dark:text-white leading-none">{np.label}</h5>
                                    </div>
                                    <div className="px-2 py-1 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-600 border border-indigo-500/20 uppercase tracking-tighter">
                                        {isLoadBalancer ? `LoadBalancer: ${np.port}` : `NodePort: ${np.node_port}`}
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">Available Endpoints</p>
                                    {isLoadBalancer ? (
                                        np.load_balancer_ips.length === 0 ? (
                                            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-500 italic">
                                                Pending LoadBalancer IP/Hostname...
                                            </div>
                                        ) : (
                                            np.load_balancer_ips.map((ip, j) => {
                                                const epValue = np.scheme ? `${np.scheme}://${ip}:${np.port}` : `${ip}:${np.port}`;
                                                return (
                                                    <div key={j} className="flex flex-col gap-2 p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                                                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight truncate">Load Balancer Address</span>
                                                        <div className="flex items-center justify-between gap-3 pt-0 text-left">
                                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                                <span className="text-[10px] font-bold text-slate-400 shrink-0 uppercase tracking-wider w-8">IP/Host</span>
                                                                {np.scheme ? (
                                                                    <a
                                                                        href={epValue}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="text-xs font-mono text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 truncate px-2 py-1 bg-slate-50 dark:bg-slate-950 rounded border border-slate-100 dark:border-slate-800/40 text-left hover:underline flex-1 min-w-0"
                                                                        title="Open URL"
                                                                    >
                                                                        {epValue}
                                                                    </a>
                                                                ) : (
                                                                    <code className="text-xs font-mono text-emerald-600 dark:text-emerald-400 truncate px-2 py-1 bg-slate-50 dark:bg-slate-950 rounded border border-slate-100 dark:border-slate-800/40 text-left flex-1 min-w-0">
                                                                        {epValue}
                                                                    </code>
                                                                )}
                                                            </div>
                                                            <div className="flex items-center gap-1 shrink-0">
                                                                {np.scheme && (
                                                                    <a
                                                                        href={epValue}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="p-1.5 text-slate-400 hover:text-blue-500 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800 rounded"
                                                                        title="Open in new tab"
                                                                    >
                                                                        <ExternalLink size={12} />
                                                                    </a>
                                                                )}
                                                                <button
                                                                    onClick={() => navigator.clipboard.writeText(epValue)}
                                                                    className="p-1.5 text-slate-400 hover:text-blue-500 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800 rounded"
                                                                    title="Copy endpoint"
                                                                >
                                                                    <Copy size={12} />
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })
                                        )
                                    ) : (
                                        clusterNodes?.map((node, j) => {
                                            const endpointsToShow = [];
                                            if (node.ipv4) {
                                                endpointsToShow.push({
                                                    type: 'IPv4',
                                                    value: np.scheme ? `${np.scheme}://${node.ipv4}:${np.node_port}` : `${node.ipv4}:${np.node_port}`
                                                });
                                            }
                                            if (node.ipv6) {
                                                endpointsToShow.push({
                                                    type: 'IPv6',
                                                    value: np.scheme ? `${np.scheme}://[${node.ipv6}]:${np.node_port}` : `[${node.ipv6}]:${np.node_port}`
                                                });
                                            }

                                            if (endpointsToShow.length === 0) return null;

                                            return (
                                                <div key={j} className="flex flex-col gap-2 p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tight truncate">{node.hostname}</span>
                                                    {endpointsToShow.map((ep, k) => (
                                                        <div key={k} className="flex items-center justify-between gap-3 border-t first:border-t-0 pt-2.5 first:pt-0 border-slate-100 dark:border-slate-800/50">
                                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                                <span className="text-[10px] font-bold text-slate-400 shrink-0 uppercase tracking-wider w-8">{ep.type}</span>
                                                                {np.scheme ? (
                                                                    <a
                                                                        href={ep.value}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="text-xs font-mono text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 truncate px-2 py-1 bg-slate-50 dark:bg-slate-950 rounded border border-slate-100 dark:border-slate-800/40 text-left hover:underline flex-1 min-w-0"
                                                                        title="Open URL"
                                                                    >
                                                                        {ep.value}
                                                                    </a>
                                                                ) : (
                                                                    <code className="text-xs font-mono text-emerald-600 dark:text-emerald-400 truncate px-2 py-1 bg-slate-50 dark:bg-slate-950 rounded border border-slate-100 dark:border-slate-800/40 text-left flex-1 min-w-0">
                                                                        {ep.value}
                                                                    </code>
                                                                )}
                                                            </div>
                                                            <div className="flex items-center gap-1 shrink-0">
                                                                {np.scheme && (
                                                                    <a
                                                                        href={ep.value}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="p-1.5 text-slate-400 hover:text-blue-500 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800 rounded"
                                                                        title="Open in new tab"
                                                                    >
                                                                        <ExternalLink size={12} />
                                                                    </a>
                                                                )}
                                                                <button
                                                                    onClick={() => navigator.clipboard.writeText(ep.value)}
                                                                    className="p-1.5 text-slate-400 hover:text-blue-500 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800 rounded"
                                                                    title="Copy endpoint"
                                                                >
                                                                    <Copy size={12} />
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {(guideText || cliInfo) && (
                    <div className="space-y-4">
                        {guideText && (
                            <div className="flex items-start gap-4 p-4 rounded-xl bg-blue-500/5 border border-blue-500/10">
                                <AlertCircle className="text-blue-500 shrink-0 mt-0.5" size={20} />
                                <div>
                                    <p className="text-sm font-bold text-slate-900 dark:text-white tracking-tight">{guideTitle}</p>
                                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 leading-relaxed" dangerouslySetInnerHTML={{ __html: guideText }} />
                                </div>
                            </div>
                        )}

                        {cliInfo && (
                            <div className={cn(
                                "flex flex-col rounded-2xl border overflow-hidden",
                                darkMode ? 'bg-slate-950/80 border-slate-800' : 'bg-slate-900 border-slate-700'
                            )}>
                                <div className={cn("flex border-b p-1 items-center justify-between", darkMode ? 'border-slate-800' : 'border-slate-700')}>
                                    <div className="flex p-1 gap-1">
                                        <button className="px-4 py-1.5 text-xs font-bold uppercase rounded-lg bg-slate-700 text-white shadow-inner">{cliLanguage}</button>
                                        {cliInfo.languageButtons && cliInfo.languageButtons.map((btn, i) => (
                                            <button key={i} className="px-4 py-1.5 text-xs font-bold uppercase rounded-lg text-slate-500 hover:text-slate-300">{btn}</button>
                                        ))}
                                    </div>
                                    <div className="px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest">{cliTitle}</div>
                                </div>
                                <div className="p-6 relative group">
                                    <pre className="text-sm font-mono text-blue-400 leading-relaxed overflow-x-auto whitespace-pre-wrap">
                                        {cliInfo.command}
                                    </pre>
                                    <button
                                        onClick={() => navigator.clipboard.writeText(cliInfo.copyValue || cliInfo.command)}
                                        className="absolute top-4 right-4 p-2 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
                                    >
                                        <Copy size={16} />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </ServiceBlock>
    );
};

export const ExternalAccessBlock = ({ darkMode, links, icon = ExternalLink }) => {
    const IconComponent = icon;
    return (
        <ServiceBlock darkMode={darkMode} icon={IconComponent} iconColorClass="text-blue-500" iconBgClass="bg-blue-500/10" title="External Web Access">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {links.map((link, i) => (
                    <div key={i} className="p-5 border rounded-2xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 flex flex-col group/item relative h-full">
                        <div className="flex items-center justify-between mb-2">
                            <h5 className="text-lg font-bold text-slate-900 dark:text-white leading-none">{link.label}</h5>
                        </div>
                        <div className="mt-2 flex items-center justify-between gap-4">
                            <a
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs font-mono text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 truncate px-2 py-1 bg-slate-50 dark:bg-slate-950 rounded border border-slate-100 dark:border-slate-800/40 text-left hover:underline flex-1 min-w-0"
                            >
                                {link.url}
                            </a>
                            <a
                                href={link.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-1.5 text-slate-400 hover:text-blue-500 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800 rounded shrink-0 border dark:border-slate-800"
                                title="Open link"
                            >
                                <IconComponent size={14} />
                            </a>
                        </div>
                        {link.description && (
                            <p className="mt-4 text-xs text-slate-500 leading-relaxed">{link.description}</p>
                        )}
                    </div>
                ))}
            </div>
        </ServiceBlock>
    );
};

export const CredentialField = ({ label, value, isMasked }) => {
    const [showPassword, setShowPassword] = useState(false);
    
    return (
        <div className="p-3 border rounded-xl group relative bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 h-full">
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">{label}</p>
            <div className="flex items-center justify-between">
                <span className={cn("text-sm font-mono truncate pr-4", isMasked && !showPassword ? "text-slate-500" : "text-slate-700 dark:text-slate-200")}>
                    {isMasked ? (showPassword ? (value || "pending") : "••••••••••••••••") : (value || 'pending')}
                </span>
                <div className="flex items-center gap-2">
                    {isMasked && (
                        <button onClick={() => setShowPassword(!showPassword)} className="text-slate-400 hover:text-slate-600 transition-colors">
                            {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                    )}
                    <button onClick={() => navigator.clipboard.writeText(value || "")} className={cn("text-slate-400 hover:text-blue-500 transition-colors", isMasked ? "" : "opacity-0 group-hover:opacity-100")}><Copy size={14} /></button>
                </div>
            </div>
        </div>
    );
};

export const CredentialBlock = ({ darkMode, credentials, caCert }) => (
    <ServiceBlock darkMode={darkMode} icon={Lock} iconColorClass="text-blue-400" iconBgClass="bg-blue-500/10" title="Cluster Credentials">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {credentials.map((cred, i) => (
                <div key={i}>
                    <CredentialField label={cred.label} value={cred.value} isMasked={cred.isMasked} />
                </div>
            ))}
        </div>

        {caCert && (
            <div className="mt-6 animate-in slide-in-from-top-2 duration-300">
                <div className="p-4 border rounded-xl bg-slate-50 border-slate-200 dark:bg-slate-950/50 dark:border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">CA Certificate</p>
                        <button
                            onClick={() => navigator.clipboard.writeText(caCert)}
                            className="text-xs font-bold text-blue-500 hover:text-blue-400 flex items-center gap-1.5 transition-colors"
                        >
                            <Copy size={12} /> COPY CERTIFICATE
                        </button>
                    </div>
                    <div className="bg-slate-900 rounded-lg p-3 relative group text-emerald-400/90">
                        <pre className="text-[10px] font-mono leading-tight overflow-x-auto max-h-[120px] scrollbar-thin scrollbar-thumb-slate-700 whitespace-pre-wrap">
                            {caCert}
                        </pre>
                    </div>
                </div>
            </div>
        )}
    </ServiceBlock>
);
