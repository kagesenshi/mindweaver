import React, { useState, useRef, useEffect } from 'react';
import { LogOut } from 'lucide-react';
import { cn } from '../utils/cn';
import { useAuth } from '../providers/AuthProvider';

const UserProfilePanel = ({ user, darkMode, isCollapsed }) => {
    const { logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const panelRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (panelRef.current && !panelRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);

    return (
        <div className="p-4 border-t border-slate-200 dark:border-slate-800/50">
            <div className="relative w-full" ref={panelRef}>
                {isOpen && (
                    <div
                        className={cn(
                            "absolute bottom-[calc(100%-1px)] left-0 right-0 rounded-t-xl rounded-b-none border border-b-0 p-1.5 shadow-xl transition-all animate-in slide-in-from-bottom-2 fade-in zoom-in-95 duration-200 z-40 ring-2 ring-blue-500/20 border-blue-500/50",
                            "bg-white dark:bg-slate-900"
                        )}
                    >
                        <button
                            onClick={logout}
                            className={cn(
                                "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors text-sm font-bold",
                                darkMode
                                    ? "text-slate-400 hover:text-rose-400 hover:bg-rose-500/10"
                                    : "text-slate-600 hover:text-rose-600 hover:bg-rose-50"
                            )}
                        >
                            <LogOut size={18} />
                            {!isCollapsed && <span>Log Out</span>}
                        </button>
                    </div>
                )}

                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className={cn(
                        "w-full mw-panel flex items-center transition-all duration-300 hover:ring-2 hover:ring-blue-500/20 active:scale-[0.98] outline-none relative",
                        isCollapsed ? "justify-center p-0" : "gap-3 p-2",
                        isOpen ? "rounded-t-none ring-2 ring-blue-500/20 border-blue-500/50 border-t-0 z-50 rounded-b-xl overflow-visible" : "rounded-xl"
                    )}
                >
                    {isOpen && (
                        <div className="absolute -top-1 left-0 right-0 h-2 bg-white dark:bg-slate-900 z-50" />
                    )}
                    <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center text-blue-400 text-lg font-bold border border-blue-500/30 shrink-0 relative z-10">
                        {user ? (user.display_name || user.name || user.email || 'U').substring(0, 2).toUpperCase() : 'U'}
                    </div>
                    {!isCollapsed && (
                        <div className="overflow-hidden text-left relative z-10">
                            <p className={cn(
                                "text-lg font-bold truncate",
                                darkMode ? 'text-white' : 'text-slate-900'
                            )}>
                                {user?.display_name || user?.name || user?.email || 'Guest User'}
                            </p>
                            {user?.email && (
                                <p className="text-base text-slate-500 truncate" title={user.email}>
                                    {user.email}
                                </p>
                            )}
                        </div>
                    )}
                </button>
            </div>
        </div>
    );
};

export default UserProfilePanel;
