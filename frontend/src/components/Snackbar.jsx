import React, { useEffect, useState, useCallback } from 'react';
import { X, AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';
import { cn } from '../utils/cn';

const Snackbar = ({ message, type = 'error', onClose, duration = 5000 }) => {
    const [isExiting, setIsExiting] = useState(false);

    const handleClose = useCallback(() => {
        setIsExiting(true);
        setTimeout(onClose, 300); // Wait for animation
    }, [onClose]);

    useEffect(() => {
        const timer = setTimeout(() => {
            handleClose();
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, handleClose]);

    const icons = {
        error: <AlertCircle size={20} />,
        success: <CheckCircle2 size={20} />,
        info: <Info size={20} />,
        warning: <AlertTriangle size={20} />
    };

    const styles = {
        error: "bg-rose-600 text-white shadow-rose-600/20",
        success: "bg-emerald-600 text-white shadow-emerald-600/20",
        info: "bg-slate-800 text-white shadow-slate-800/20",
        warning: "bg-amber-500 text-white shadow-amber-500/20"
    };

    return (
        <div className={cn(
            "fixed top-0 left-0 right-0 z-[9999] animate-in slide-in-from-top-full duration-500 pointer-events-auto",
            isExiting && "animate-out fade-out slide-out-to-top-full"
        )}>
            <div className={cn(
                "flex items-center justify-center gap-6 p-3 shadow-2xl transition-all",
                styles[type] || styles.info
            )}>
                <div className="flex items-center gap-3 max-w-7xl w-full px-8">
                    <div className="shrink-0 scale-90">
                        {icons[type] || icons.info}
                    </div>
                    <div className="flex-1 text-xs font-black tracking-[0.15em] py-0.5 uppercase text-center">
                        {message}
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-1.5 rounded-lg hover:bg-white/10 transition-colors shrink-0"
                    >
                        <X size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Snackbar;
