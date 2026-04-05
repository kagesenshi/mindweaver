import { NavLink, useLocation } from 'react-router-dom';
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
    Boxes,
    Globe,
} from 'lucide-react';
import { cn } from '../utils/cn';
import { useAuth } from '../providers/AuthProvider';
import { Tooltip } from './Tooltip';
import UserProfilePanel from './UserProfilePanel';

const NAV_ITEMS = [
    { name: 'Fleet Overview', to: '/', icon: Monitor },
];

const ENVIRONMENT_ITEMS = [
    { name: 'K8s Clusters', to: '/k8s_clusters', icon: Server },
    { name: 'LDAP Configs', to: '/ldap-configs', icon: ShieldCheck },
    { name: 'Projects', to: '/projects', icon: Briefcase },
];

const DATA_SOURCE_ITEMS = [
    { name: 'Database Sources', to: '/database-sources', icon: Database },
    { name: 'Web Sources', to: '/web-sources', icon: Globe },
    { name: 'API Sources', to: '/api-sources', icon: Layers },
    { name: 'Streaming Sources', to: '/streaming-sources', icon: RefreshCcw },
];

const CONNECTIVITY_ITEMS = [
    { name: 'S3 Storages', to: '/s3-storages', icon: HardDrive },
];


const INFRA_ITEMS = [
    { name: 'PostgreSQL', to: '/platform/pgsql', icon: Database },
    { name: 'Hive Metastore', to: '/platform/hive-metastore', icon: Boxes },
    { name: 'Trino', to: '/platform/trino', icon: Wind },
    { name: 'Apache Spark', to: '/platform/spark', icon: Layers },
    { name: 'Apache Airflow', to: '/platform/airflow', icon: Activity },
    { name: 'Apache Superset', to: '/platform/superset', icon: BarChart3 },
    { name: 'Apache Kafka', to: '/platform/kafka', icon: RefreshCcw },
];

const Sidebar = ({ darkMode, isCollapsed, toggleSidebar, onNavItemClick }) => {
    const { user } = useAuth();
    const location = useLocation();
    const sidebarBg = darkMode ? "bg-[#0c0e12]" : "bg-white";
    const borderCol = darkMode ? "border-slate-800" : "border-slate-200";

    const handleClick = (to) => {
        if (location.pathname === to) {
            onNavItemClick?.();
        }
    };

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
                            onClick={() => handleClick(item.to)}
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

                {/* Environment Section */}
                <div className={cn("transition-all duration-300", isCollapsed ? "py-4 flex justify-center" : "pt-2 pb-2")}>
                    {isCollapsed ? (
                        <div className="w-8 h-px bg-slate-200 dark:bg-slate-800" />
                    ) : (
                        <div className="mw-sidebar-section">Environment</div>
                    )}
                </div>

                {ENVIRONMENT_ITEMS.map((item) => (
                    <Tooltip key={item.to} content={item.name} disabled={!isCollapsed} side="right">
                        <NavLink
                            to={item.to}
                            onClick={() => handleClick(item.to)}
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

                {/* Connectivity Section */}
                <div className={cn("transition-all duration-300", isCollapsed ? "py-4 flex justify-center" : "pt-2 pb-2")}>
                    {isCollapsed ? (
                        <div className="w-8 h-px bg-slate-200 dark:bg-slate-800" />
                    ) : (
                        <div className="mw-sidebar-section">Connectivity</div>
                    )}
                </div>

                {CONNECTIVITY_ITEMS.map((item) => (
                    <Tooltip key={item.to} content={item.name} disabled={!isCollapsed} side="right">
                        <NavLink
                            to={item.to}
                            onClick={() => handleClick(item.to)}
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

                {/* Data Sources Section */}
                <div className={cn("transition-all duration-300", isCollapsed ? "py-4 flex justify-center" : "pt-2 pb-2")}>
                    {isCollapsed ? (
                        <div className="w-8 h-px bg-slate-200 dark:bg-slate-800" />
                    ) : (
                        <div className="mw-sidebar-section">Data Sources</div>
                    )}
                </div>

                {DATA_SOURCE_ITEMS.map((item) => (
                    <Tooltip key={item.to} content={item.name} disabled={!isCollapsed} side="right">
                        <NavLink
                            to={item.to}
                            onClick={() => handleClick(item.to)}
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

                {/* Infrastructure Section */}
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
                            onClick={() => handleClick(item.to)}
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

            <UserProfilePanel
                user={user}
                darkMode={darkMode}
                isCollapsed={isCollapsed}
            />
        </aside>
    );
};

export default Sidebar;
