/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/
import React, { useState } from 'react';
import { Users, ShieldAlert, Key, Edit2, Trash2, CheckCircle2, XCircle } from 'lucide-react';
import Modal from '../../components/Modal';
import DynamicForm from '../../components/DynamicForm';
import GenericListingView from '../../components/GenericListingView';
import apiClient from '../../services/api';
import { useNotification } from '../../providers/NotificationProvider';

const ListingView = ({
    darkMode,
    usersHook
}) => {
    const { items: users, loading, deleteItem: deleteUser, fetchItems: fetchUsers } = usersHook;
    const { showSuccess, showError } = useNotification();
    
    const [editItem, setEditItem] = useState(null);
    const [changePasswordItem, setChangePasswordItem] = useState(null);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [submittingPassword, setSubmittingPassword] = useState(false);
    const [passwordError, setPasswordError] = useState('');

    const renderSubtitle = (userItem) => (
        <span className="text-slate-400 dark:text-slate-500 text-sm">
            {userItem.email} {userItem.title ? `| ${userItem.title}` : ''}
        </span>
    );

    const renderBadges = (userItem) => {
        const badges = [];
        if (userItem.is_superadmin) {
            badges.push({ text: "SUPERADMIN", variant: "mw-badge-danger" });
        }
        if (userItem.is_active) {
            badges.push({ text: "ACTIVE", variant: "mw-badge-success" });
        } else {
            badges.push({ text: "INACTIVE", variant: "mw-badge-neutral" });
        }
        return badges;
    };

    const renderIcon = (userItem) => {
        return userItem.is_superadmin ? ShieldAlert : Users;
    };

    const handleChangePasswordSubmit = async (e) => {
        e.preventDefault();
        setPasswordError('');
        
        if (newPassword.length < 8) {
            setPasswordError('Password must be at least 8 characters long.');
            return;
        }
        if (newPassword !== confirmPassword) {
            setPasswordError('Passwords do not match.');
            return;
        }

        setSubmittingPassword(true);
        try {
            await apiClient.post(`/users/${changePasswordItem.id}/_change_password`, {
                password: newPassword
            });
            showSuccess('Password updated successfully');
            setChangePasswordItem(null);
            setNewPassword('');
            setConfirmPassword('');
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || 'Failed to update password';
            setPasswordError(typeof msg === 'string' ? msg : JSON.stringify(msg));
            showError('Failed to update password');
        } finally {
            setSubmittingPassword(false);
        }
    };

    const renderActions = (item, state, { onEdit, onDelete }) => {
        return (
            <div className="flex items-center gap-2">
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        setChangePasswordItem(item);
                        setPasswordError('');
                        setNewPassword('');
                        setConfirmPassword('');
                    }}
                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-amber-500"
                    title="Change Password"
                >
                    <Key size={18} />
                </button>
                {onEdit && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onEdit(item);
                        }}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-blue-500"
                        title="Edit"
                    >
                        <Edit2 size={18} />
                    </button>
                )}
                {onDelete && (
                    <button
                        onClick={(e) => onDelete(e, item)}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-red-500"
                        title="Delete"
                    >
                        <Trash2 size={18} />
                    </button>
                )}
            </div>
        );
    };

    return (
        <>
            <GenericListingView
                title="Local User Management"
                description="Manage local users, administrators, credentials, and permissions for the management platform."
                items={users}
                loading={loading}
                fetchItems={fetchUsers}
                deleteItem={deleteUser}
                onSelectItem={(usr) => setEditItem(usr)}
                onEditItem={(usr) => setEditItem(usr)}
                icon={Users}
                entityPath="/users"
                createConfig={{
                    title: "Create Local User",
                    buttonText: "CREATE USER",
                    initialData: {
                        is_active: true,
                        is_superadmin: false
                    },
                    onSuccess: () => {},
                }}
                searchPlaceholder="Search Users..."
                emptyState={{
                    title: "No local users found",
                    description: "Create your first local user to get started.",
                    icon: <Users size={48} className="text-slate-700" />
                }}
                renderSubtitle={renderSubtitle}
                renderBadges={renderBadges}
                renderIcon={renderIcon}
                renderActions={renderActions}
                deleteModalConfig={{
                    title: "Delete User",
                    message: "Are you sure you want to delete this user? They will immediately lose all access to the platform."
                }}
                darkMode={darkMode}
                searchFields={["name", "display_name", "email", "title"]}
            />

            {/* Edit User Modal */}
            <Modal
                isOpen={!!editItem}
                onClose={() => setEditItem(null)}
                title="Edit Local User"
                darkMode={darkMode}
            >
                <div className="space-y-4">
                    {editItem && (
                        <DynamicForm
                            entityPath="/users"
                            mode="edit"
                            darkMode={darkMode}
                            initialData={editItem}
                            onSuccess={() => {
                                fetchUsers();
                                setEditItem(null);
                            }}
                            onCancel={() => setEditItem(null)}
                        />
                    )}
                </div>
            </Modal>

            {/* Change Password Modal */}
            <Modal
                isOpen={!!changePasswordItem}
                onClose={() => setChangePasswordItem(null)}
                title={changePasswordItem ? `Change Password for ${changePasswordItem.display_name || changePasswordItem.name}` : 'Change Password'}
                darkMode={darkMode}
            >
                <form onSubmit={handleChangePasswordSubmit} className="space-y-6">
                    {passwordError && (
                        <div className="p-4 rounded-xl border flex items-center gap-3 text-sm font-bold bg-rose-500/10 border-rose-500/20 text-rose-600">
                            <XCircle size={18} />
                            {passwordError}
                        </div>
                    )}
                    
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">
                            New Password
                        </label>
                        <input
                            type="password"
                            required
                            placeholder="Min 8 characters"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className="w-full px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">
                            Confirm New Password
                        </label>
                        <input
                            type="password"
                            required
                            placeholder="Re-enter password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                        <button
                            type="button"
                            onClick={() => setChangePasswordItem(null)}
                            className="mw-btn-secondary px-6 py-3"
                        >
                            CANCEL
                        </button>
                        <button
                            type="submit"
                            disabled={submittingPassword}
                            className="mw-btn-primary px-6 py-3"
                        >
                            {submittingPassword ? 'SAVING...' : 'CHANGE PASSWORD'}
                        </button>
                    </div>
                </form>
            </Modal>
        </>
    );
};

export default ListingView;
