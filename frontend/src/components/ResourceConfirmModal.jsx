import React, { useState, useEffect } from 'react';
import { AlertTriangle, Trash2, Zap } from 'lucide-react';
import Modal from './Modal';
import { cn } from '../utils/cn';

const ResourceConfirmModal = ({
    isOpen,
    onClose,
    onConfirm,
    resourceName,
    darkMode,
    title = "Confirm Action",
    message = "This action is permanent and cannot be undone.",
    confirmText = "CONFIRM",
    icon: Icon = AlertTriangle,
    variant = "danger" // "danger" or "warning"
}) => {
    const [inputValue, setInputValue] = useState('');

    useEffect(() => {
        if (isOpen) {
            setInputValue('');
        }
    }, [isOpen]);

    const isMatch = inputValue === resourceName;

    const handleConfirm = () => {
        if (isMatch) {
            onConfirm(inputValue);
            onClose();
        }
    };

    const variantStyles = {
        danger: {
            iconBox: "bg-rose-500/10 text-rose-500",
            header: "text-rose-500",
            button: "bg-rose-500 hover:bg-rose-600 shadow-rose-500/20",
            inputRing: "focus:ring-rose-500/20",
            matchText: "text-rose-500 bg-rose-500/5 border-rose-500/10"
        },
        warning: {
            iconBox: "bg-amber-500/10 text-amber-500",
            header: "text-amber-500",
            button: "bg-amber-500 hover:bg-amber-600 shadow-amber-500/20",
            inputRing: "focus:ring-amber-500/20",
            matchText: "text-amber-500 bg-amber-500/5 border-amber-500/10"
        },
        info: {
            iconBox: "bg-blue-500/10 text-blue-500",
            header: "text-blue-500",
            button: "bg-blue-500 hover:bg-blue-600 shadow-blue-500/20",
            inputRing: "focus:ring-blue-500/20",
            matchText: "text-blue-500 bg-blue-500/5 border-blue-500/10"
        }
    };

    const style = variantStyles[variant] || variantStyles.danger;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={title}
            darkMode={darkMode}
            maxWidth="max-w-lg"
        >
            <div className="space-y-6">
                <div className="flex flex-col items-center text-center space-y-4">
                    <div className={cn("w-16 h-16 rounded-full flex items-center justify-center shadow-inner", style.iconBox)}>
                        <Icon size={32} />
                    </div>
                    <div className="space-y-2">
                        <h4 className={cn("text-xl font-bold uppercase tracking-tight", style.header)}>Dangerous Action</h4>
                        <p className="text-slate-500 dark:text-slate-400 leading-relaxed px-4">
                            {message} For resource: <strong className="text-slate-900 dark:text-slate-100 font-mono">{resourceName}</strong>
                        </p>
                    </div>
                </div>

                <div className="space-y-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                    <p className="text-sm font-bold text-slate-700 dark:text-slate-300 text-center">
                        Please type <span className={cn("font-mono select-all px-1.5 py-0.5 rounded border", style.matchText)}>{resourceName}</span> to confirm.
                    </p>
                    <div className="px-8">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Type resource name..."
                            className={cn(
                                "w-full px-4 py-3 rounded-xl border text-center font-mono text-lg transition-all focus:outline-none focus:ring-2",
                                darkMode
                                    ? cn("bg-slate-900 border-slate-800 text-white", style.inputRing)
                                    : cn("bg-slate-50 border-slate-200 text-slate-900", style.inputRing)
                            )}
                            autoFocus
                        />
                    </div>
                </div>

                <div className="flex flex-col gap-3 pt-4 px-8">
                    <button
                        onClick={handleConfirm}
                        disabled={!isMatch}
                        className={cn(
                            "w-full py-4 rounded-xl flex items-center justify-center gap-3 font-black uppercase tracking-[0.2em] transition-all",
                            isMatch
                                ? cn("text-white shadow-lg active:scale-[0.98]", style.button)
                                : "bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                        )}
                    >
                        {confirmText}
                    </button>
                    <button
                        onClick={onClose}
                        className="w-full py-3 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 font-bold uppercase tracking-widest transition-colors"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </Modal>
    );
};

export default ResourceConfirmModal;
