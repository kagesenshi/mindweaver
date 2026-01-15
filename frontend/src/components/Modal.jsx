import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { cn } from '../utils/cn';

const Modal = ({ isOpen, onClose, title, children, darkMode, maxWidth = "max-w-4xl" }) => {
    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300"
                onClick={onClose}
            />

            {/* Content */}
            <div className={cn(
                "w-full bg-white dark:bg-[#0c0e12] border border-slate-200 dark:border-slate-800 rounded-[40px] shadow-2xl relative z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-300",
                maxWidth
            )}>
                <div className="flex items-center justify-between p-8 border-b border-slate-100 dark:border-slate-800">
                    <h3 className="text-xl font-bold dark:text-white uppercase tracking-tight">{title}</h3>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full text-slate-500 transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                <div className="p-8 max-h-[80vh] overflow-y-auto">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default Modal;
