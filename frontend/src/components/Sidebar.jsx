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
    HardDrive
} from 'lucide-react';
import { cn } from '../utils/cn';

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

const Sidebar = ({ darkMode }) => {
    const sidebarBg = darkMode ? "bg-[#0c0e12]" : "bg-white";
    const borderCol = darkMode ? "border-slate-800" : "border-slate-200";

    return (
        <aside className={cn(
            "w-64 border-r flex flex-col fixed h-full z-50 transition-colors duration-300",
            sidebarBg,
            borderCol
        )}>
            <div className={cn("p-6 border-b flex items-center gap-3", borderCol)}>
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-600/20">
                    <Layers className="text-white" size={20} />
                </div>
                <h1 className={cn(
                    "text-2xl font-bold tracking-tight",
                    darkMode ? 'text-white' : 'text-slate-900'
                )}>
                    Mindweaver
                </h1>
            </div>

            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                {NAV_ITEMS.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) => cn(
                            "mw-nav-item",
                            isActive
                                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                                : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent'
                        )}
                    >
                        <item.icon size={20} />
                        {item.name}
                    </NavLink>
                ))}

                <div className="mw-sidebar-section">
                    Infrastructure
                </div>

                {INFRA_ITEMS.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) => cn(
                            "mw-nav-item",
                            isActive
                                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
                                : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent'
                        )}
                    >
                        <div className="flex items-center gap-2">
                            <item.icon size={20} className={cn(
                                "transition-colors",
                                // We'll leave the logic for active state coloring here if needed
                            )} />
                            {item.name}
                        </div>
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 border-t border-slate-200 dark:border-slate-800/50">
                <div className="mw-panel flex items-center gap-3 p-2 rounded-xl">
                    <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center text-blue-400 text-base font-bold border border-blue-500/30">
                        JD
                    </div>
                    <div className="overflow-hidden">
                        <p className={cn(
                            "text-base font-bold truncate",
                            darkMode ? 'text-white' : 'text-slate-900'
                        )}>
                            Jane Deployer
                        </p>
                        <p className="text-base text-slate-500 uppercase font-mono tracking-wider">
                            Platform Lead
                        </p>
                    </div>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
