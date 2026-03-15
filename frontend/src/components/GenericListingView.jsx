/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React, { useState, useEffect } from 'react';
import { Search, ChevronRight, Trash2, Edit2 } from 'lucide-react';
import PageLayout from './PageLayout';
import ListingItem from './ListingItem';
import ResourceConfirmModal from './ResourceConfirmModal';

const GenericListingView = ({
    title,
    description,
    items = [],
    loading,
    fetchItems,
    deleteItem,
    getItemState,
    onSelectItem,
    onEditItem,
    icon: IconComponent,
    entityPath,
    createConfig = {},
    searchPlaceholder = "Search...",
    emptyState = {},
    renderSubtitle,    renderBadges,
    renderActions,
    renderIcon,
    renderExtraItemContent,
    deleteModalConfig = {},
    darkMode,
    selectedProject,
    rowKey = "id",
    searchFields = ["name", "title", "id"],
    pollInterval = 5000
}) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [itemStates, setItemStates] = useState({});
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [selectedItemForDelete, setSelectedItemForDelete] = useState(null);

    const filteredItems = items.filter(item => {
        const matchesProject = !selectedProject || !item.project_id || item.project_id === selectedProject.id;
        const matchesSearch = searchFields.some(field => 
            String(item[field] || '').toLowerCase().includes(searchTerm.toLowerCase())
        );
        return matchesProject && matchesSearch;
    });

    useEffect(() => {
        let timer;
        const fetchStates = async () => {
            if (!getItemState || items.length === 0) return;
            const states = {};
            await Promise.all(items.map(async (item) => {
                try {
                    const state = await getItemState(item[rowKey]);
                    states[item[rowKey]] = state;
                } catch (e) {
                    console.error(`Failed to fetch state for item ${item[rowKey]}`, e);
                }
            }));
            setItemStates(states);
        };

        if (getItemState && items.length > 0) {
            fetchStates();
            timer = setInterval(fetchStates, pollInterval);
        }

        return () => {
            if (timer) clearInterval(timer);
        };
    }, [items, getItemState, rowKey, pollInterval]);

    const handleDeleteClick = (e, item) => {
        e.stopPropagation();
        setSelectedItemForDelete(item);
        setIsDeleteModalOpen(true);
    };

    const handleConfirmDelete = async (typedName) => {
        if (selectedItemForDelete && deleteItem) {
            await deleteItem(selectedItemForDelete[rowKey], typedName);
            setIsDeleteModalOpen(false);
            setSelectedItemForDelete(null);
            if (fetchItems) await fetchItems();
        }
    };

    return (
        <React.Fragment>
            <PageLayout
                title={title}
                description={description}
                createConfig={{
                    ...createConfig,
                    entityPath: entityPath,
                    initialData: { ...createConfig.initialData, project_id: selectedProject?.id },
                    onSuccess: async () => {
                        if (createConfig.onSuccess) await createConfig.onSuccess();
                        if (fetchItems) await fetchItems();
                    }
                }}
                searchQuery={searchTerm}
                onSearchChange={(e) => setSearchTerm(e.target.value)}
                searchPlaceholder={searchPlaceholder}
                isLoading={loading}
                isEmpty={filteredItems.length === 0}
                emptyState={emptyState}
            >
                <div className="grid grid-cols-1 gap-4">
                    {filteredItems.map(item => {
                        const state = itemStates[item[rowKey]] || {};
                        
                        return (
                            <div key={item[rowKey]} className="mw-list-wrapper">
                                <ListingItem
                                    icon={renderIcon ? renderIcon(item, state) : IconComponent}
                                    title={item.title || item.name}
                                    badges={renderBadges ? renderBadges(item, state) : []}
                                    subtitle={renderSubtitle ? renderSubtitle(item, state) : item.description}
                                    onClick={() => onSelectItem && onSelectItem(item)}
                                    actions={
                                        <div className="flex items-center gap-2">
                                            {renderActions ? renderActions(item, state, { onEdit: onEditItem, onDelete: handleDeleteClick }) : (
                                                <React.Fragment>
                                                    {onEditItem && (
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                onEditItem(item);
                                                            }}
                                                            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                                                            title="Edit"
                                                        >
                                                            <Edit2 size={18} />
                                                        </button>
                                                    )}
                                                    {deleteItem && (
                                                        <button
                                                            onClick={(e) => handleDeleteClick(e, item)}
                                                            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                                                            title="Delete"
                                                        >
                                                            <Trash2 size={18} />
                                                        </button>
                                                    )}
                                                    <div className="w-px h-8 bg-slate-200 dark:bg-slate-800 mx-2" />
                                                    <ChevronRight size={20} className="text-slate-300 dark:text-slate-600" />
                                                </React.Fragment>
                                            )}
                                        </div>
                                    }
                                />
                                {renderExtraItemContent && renderExtraItemContent(item, state)}
                            </div>
                        );
                    })}
                </div>
            </PageLayout>


            {isDeleteModalOpen && selectedItemForDelete && (
                <ResourceConfirmModal
                    isOpen={isDeleteModalOpen}
                    onClose={() => {
                        setIsDeleteModalOpen(false);
                        setSelectedItemForDelete(null);
                    }}
                    onConfirm={handleConfirmDelete}
                    resourceName={selectedItemForDelete.name || selectedItemForDelete.title}
                    darkMode={darkMode}
                    title={deleteModalConfig.title || `Delete ${title}`}
                    message={deleteModalConfig.message || "Are you sure you want to delete this resource?"}
                />
            )}
        </React.Fragment>
    );
};

export default GenericListingView;
