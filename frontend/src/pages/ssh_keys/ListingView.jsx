/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React, { useState } from 'react';
import { Key, Copy, Check } from 'lucide-react';
import Modal from '../../components/Modal';
import GenericListingView from '../../components/GenericListingView';
import { cn } from '../../utils/cn';

const SSHPublicKeyCopy = ({ publicKey, darkMode }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(publicKey);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className={cn(
            "mt-2 p-3 rounded-lg border flex items-center justify-between gap-3 text-sm font-mono",
            darkMode ? "bg-slate-900/50 border-slate-800 text-slate-300" : "bg-slate-50 border-slate-200 text-slate-600"
        )}>
            <div className="break-all flex-1 select-all select-text">{publicKey}</div>
            <button
                type="button"
                onClick={handleCopy}
                className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-800 rounded transition-colors text-slate-400 hover:text-blue-500 flex items-center gap-1 shrink-0"
                title="Copy Public Key"
            >
                {copied ? <Check size={16} className="text-emerald-500" /> : <Copy size={16} />}
                <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
        </div>
    );
};

const ListingView = ({
    darkMode,
    selectedProject,
    sshKeysHook
}) => {
    const { keys, loading, deleteKey, fetchKeys } = sshKeysHook;
    const [selectedKeyForDetails, setSelectedKeyForDetails] = useState(null);

    const renderSubtitle = (keyItem) => (
        <span className="uppercase text-slate-400 dark:text-slate-500 text-sm">
            {keyItem.algorithm} {keyItem.algorithm === 'rsa' ? `(${keyItem.key_size} bits)` : ''}
        </span>
    );

    return (
        <>
            <GenericListingView
                title="SSH Keys"
                description="Manage secure SSH keys. Keys are automatically generated and cannot be manually modified."
                items={keys}
                loading={loading}
                fetchItems={fetchKeys}
                deleteItem={deleteKey}
                onSelectItem={(keyItem) => setSelectedKeyForDetails(keyItem)}
                icon={Key}
                entityPath="/ssh_keys"
                createConfig={{
                    title: "Generate New SSH Key",
                    buttonText: "GENERATE KEY",
                    initialData: {
                        algorithm: 'rsa',
                        key_size: 4096
                    },
                    onSuccess: () => {},
                }}
                searchPlaceholder="Search SSH Keys..."
                emptyState={{
                    title: "No SSH Keys found",
                    description: selectedProject
                        ? `No SSH Keys configured in ${selectedProject.name}.`
                        : 'Generate your first SSH Key connection to get started.',
                    icon: <Key size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                deleteModalConfig={{
                    title: "Delete SSH Key",
                    message: "Are you sure you want to delete this SSH Key? Any Git connections using it will fail to authenticate."
                }}
                darkMode={darkMode}
                selectedProject={selectedProject}
                searchFields={["name", "title"]}
            />

            <Modal
                isOpen={!!selectedKeyForDetails}
                onClose={() => setSelectedKeyForDetails(null)}
                title="SSH Key Details"
                darkMode={darkMode}
            >
                {selectedKeyForDetails && (
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm text-slate-500 font-semibold block mb-1">Name</label>
                            <div className="text-base font-medium">{selectedKeyForDetails.name}</div>
                        </div>
                        <div>
                            <label className="text-sm text-slate-500 font-semibold block mb-1">Title</label>
                            <div className="text-base font-medium">{selectedKeyForDetails.title}</div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-sm text-slate-500 font-semibold block mb-1">Algorithm</label>
                                <div className="text-base font-medium uppercase">{selectedKeyForDetails.algorithm}</div>
                            </div>
                            <div>
                                <label className="text-sm text-slate-500 font-semibold block mb-1">Key Size</label>
                                <div className="text-base font-medium">
                                    {selectedKeyForDetails.algorithm === 'rsa' ? `${selectedKeyForDetails.key_size} bits` : 'N/A'}
                                </div>
                            </div>
                        </div>
                        <div>
                            <label className="text-sm text-slate-500 font-semibold block mb-1">Public Key (Deploy Key)</label>
                            <SSHPublicKeyCopy publicKey={selectedKeyForDetails.public_key} darkMode={darkMode} />
                        </div>
                        <div className="flex justify-end pt-2">
                            <button
                                type="button"
                                onClick={() => setSelectedKeyForDetails(null)}
                                className="mw-btn-secondary px-6 py-2 text-sm"
                            >
                                CLOSE
                            </button>
                        </div>
                    </div>
                )}
            </Modal>
        </>
    );
};

export default ListingView;
