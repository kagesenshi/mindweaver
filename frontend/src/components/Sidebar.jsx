import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    Monitor,
    Briefcase,
    Library,
    Database,
    Wind,
    Layers,
    Activity,
    BarChart3,
    RefreshCcw,
    LayoutGrid,
    Settings,
    ShieldCheck,
    Server,
    Cloud,
    HardDrive,
    ChevronLeft,
    ChevronRight,
} from 'lucide-react';
import { cn } from '../utils/cn';
import { useAuth } from '../providers/AuthProvider';
import { Tooltip } from './Tooltip';

const NAV_ITEMS = [
    { name: 'Fleet Overview', to: '/', icon: Monitor },
    { name: 'Manage Projects', to: '/projects', icon: Briefcase },
    { name: 'Data Sources', to: '/data-sources', icon: Library },
    { name: 'K8s Clusters', to: '/k8s-clusters', icon: Cloud },
];


const INFRA_ITEMS = [
    { name: 'PostgreSQL', to: '/platform/pgsql', icon: Database },
    { name: 'Trino', to: '/platform/trino', icon: Wind },
    { name: 'Apache Spark', to: '/platform/spark', icon: Layers },
    { name: 'Apache Airflow', to: '/platform/airflow', icon: Activity },
    { name: 'Apache Superset', to: '/platform/superset', icon: BarChart3 },
    { name: 'Apache Kafka', to: '/platform/kafka', icon: RefreshCcw },
];

const Sidebar = ({ darkMode, isCollapsed, toggleSidebar }) => {
    const { user } = useAuth();
    const sidebarBg = darkMode ? "bg-[#0c0e12]" : "bg-white";
    const borderCol = darkMode ? "border-slate-800" : "border-slate-200";

    return (
        <aside className={cn(
            "border-r flex flex-col fixed h-full z-[70] transition-all duration-300 ease-in-out",
            isCollapsed ? "w-20" : "w-[266px]",
            sidebarBg,
            borderCol
        )}>
            {/* Header */}
            <div className={cn("h-[81px] border-b flex items-center transition-all duration-300",
                borderCol,
                isCollapsed ? "justify-center px-0" : "px-6 gap-3"
            )}>
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shrink-0 shadow-lg shadow-blue-600/20">
                    <Layers className="text-white" size={20} />
                </div>
                {!isCollapsed && (
                    <h1 className={cn(
                        "text-2xl font-bold tracking-tight whitespace-nowrap overflow-hidden transition-opacity duration-300",
                        darkMode ? 'text-white' : 'text-slate-900'
                    )}>
                        Mindweaver
                    </h1>
                )}
            </div>

            {/* Toggle Button */}
            <button
                onClick={toggleSidebar}
                className={cn(
                    "absolute -right-4 top-[28px] w-8 h-8 rounded-full border bg-white dark:bg-slate-900 flex items-center justify-center text-slate-500 hover:text-blue-500 transition-colors z-50 shadow-sm",
                    darkMode ? "border-slate-700" : "border-slate-200"
                )}
            >
                {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            </button>

            <nav className="flex-1 p-4 space-y-1 overflow-y-auto overflow-x-hidden">
                {NAV_ITEMS.map((item) => (
                    <Tooltip key={item.to} content={item.name} disabled={!isCollapsed} side="right">
                        <NavLink
                            to={item.to}
                            className={({ isActive }) => cn(
                                "mw-nav-item flex items-center transition-all duration-200",
                                isCollapsed ? "justify-center p-2 rounded-lg" : "px-3 py-2 rounded-lg gap-3",
                                isActive
                                    ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                                    : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent'
                            )}
                        >
                            <item.icon size={20} className="shrink-0" />
                            {!isCollapsed && <span className="whitespace-nowrap overflow-hidden">{item.name}</span>}
                        </NavLink>
                    </Tooltip>
                ))}

                <div className={cn("transition-all duration-300", isCollapsed ? "py-4 flex justify-center" : "pt-6 pb-2")}>
                    {isCollapsed ? (
                        <div className="w-8 h-px bg-slate-200 dark:bg-slate-800" />
                    ) : (
                        <div className="mw-sidebar-section">Infrastructure</div>
                    )}
                </div>

                {INFRA_ITEMS.map((item) => (
                    <Tooltip key={item.to} content={item.name} disabled={!isCollapsed} side="right">
                        <NavLink
                            to={item.to}
                            className={({ isActive }) => cn(
                                "mw-nav-item flex items-center transition-all duration-200",
                                isCollapsed ? "justify-center p-2 rounded-lg" : "px-3 py-2 rounded-lg gap-3",
                                isActive
                                    ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                                    : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent'
                            )}
                        >
                            <item.icon size={20} className="shrink-0" />
                            {!isCollapsed && <span className="whitespace-nowrap overflow-hidden">{item.name}</span>}
                        </NavLink>
                    </Tooltip>
                ))}
            </nav>

            <div className="p-4 border-t border-slate-200 dark:border-slate-800/50">
                <div className={cn(
                    "mw-panel flex items-center rounded-xl transition-all duration-300",
                    isCollapsed ? "justify-center p-0" : "gap-3 p-2"
                )}>
                    <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center text-blue-400 text-lg font-bold border border-blue-500/30 shrink-0">
                        {user ? (user.display_name || user.name || user.email || 'U').substring(0, 2).toUpperCase() : 'U'}
                    </div>
                    {!isCollapsed && (
                        <div className="overflow-hidden">
                            <p className={cn(
                                "text-sm font-bold truncate",
                                darkMode ? 'text-white' : 'text-slate-900'
                            )}>
                                {user?.display_name || user?.name || user?.email || 'Guest User'}
                            </p>
                            {user?.email && (
                                <p className="text-xs text-slate-500 truncate" title={user.email}>
                                    {user.email}
                                </p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
