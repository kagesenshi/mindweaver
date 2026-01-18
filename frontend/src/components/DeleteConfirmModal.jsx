import React, { useState, useEffect } from 'react';
import { AlertTriangle, Trash2 } from 'lucide-react';
import Modal from './Modal';
import { cn } from '../utils/cn';

const DeleteConfirmModal = ({
    isOpen,
    onClose,
    onConfirm,
    resourceName,
    darkMode
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

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Confirm Deletion"
            darkMode={darkMode}
            maxWidth="max-w-lg"
        >
            <div className="space-y-6">
                <div className="flex flex-col items-center text-center space-y-4">
                    <div className="w-16 h-16 bg-rose-500/10 text-rose-500 rounded-full flex items-center justify-center shadow-inner">
                        <AlertTriangle size={32} />
                    </div>
                    <div className="space-y-2">
                        <h4 className="text-xl font-bold text-slate-900 dark:text-white uppercase tracking-tight">Dangerous Action</h4>
                        <p className="text-slate-500 dark:text-slate-400 leading-relaxed px-4">
                            This action is permanent and cannot be undone. All data and resources associated with <strong className="text-slate-900 dark:text-slate-100 font-mono">{resourceName}</strong> will be destroyed.
                        </p>
                    </div>
                </div>

                <div className="space-y-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                    <p className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-widest text-center">
                        Please type <span className="text-rose-500 font-mono select-all px-1.5 py-0.5 bg-rose-500/5 rounded border border-rose-500/10">{resourceName}</span> to confirm.
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
                                    ? "bg-slate-900 border-slate-800 text-white focus:ring-blue-500/50"
                                    : "bg-slate-50 border-slate-200 text-slate-900 focus:ring-blue-500/20"
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
                                ? "bg-rose-500 text-white hover:bg-rose-600 shadow-lg shadow-rose-500/20 active:scale-[0.98]"
                                : "bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                        )}
                    >
                        <Trash2 size={20} />
                        DELETE
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

export default DeleteConfirmModal;
