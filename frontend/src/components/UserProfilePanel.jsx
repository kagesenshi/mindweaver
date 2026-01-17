import React, { useState } from 'react';
import { LogOut } from 'lucide-react';
import { cn } from '../utils/cn';
import { useAuth } from '../providers/AuthProvider';

import Drawer from './Drawer';

const UserProfilePanel = ({ user, darkMode, isCollapsed }) => {
    const { logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="p-4 border-t border-slate-200 dark:border-slate-800/50">
            <Drawer
                isOpen={isOpen}
                onOpenChange={setIsOpen}
                placement="top"
                darkMode={darkMode}
                activeBg={darkMode ? "bg-slate-900" : "bg-white"}
                className="w-full"
                trigger={
                    <div className={cn(
                        "w-full mw-panel flex items-center gap-3 p-2",
                        isCollapsed && "justify-center p-0"
                    )}>
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
                    </div>
                }
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
            </Drawer>
        </div>
    );
};

export default UserProfilePanel;
