/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React, { useState } from 'react';
import { cn } from '../../utils/cn';
import { Plus, Trash2 } from 'lucide-react';

/**
 * AuthRoleMappingWidget - Helper component for Auth-Role Mapping fields
 * 
 * @param {string} name - Field name
 * @param {array} value - Initial array of mapping objects
 * @param {array} roles - Available roles to choose from
 * @param {function} onChange - Callback function(name, value)
 * @param {boolean} darkMode - Whether dark mode is enabled
 * @param {boolean} isImmutable - Whether the field is disabled
 */
const AuthRoleMappingWidget = ({ name, value, roles = [], onChange, darkMode, isImmutable }) => {
    // Initial load: convert array of objects to internal state
    const [items, setItems] = useState(() => {
        if (Array.isArray(value)) {
            return value.map(item => ({
                entity: item.entity || '',
                role: item.role || (roles.length > 0 ? roles[0] : '')
            }));
        }
        return [];
    });

    const inputBg = darkMode ? "bg-slate-950 border-slate-800 text-slate-200" : "bg-slate-100 border-slate-200 text-slate-900";
    const disabledBg = darkMode ? "bg-slate-900 border-slate-800 text-slate-500" : "bg-slate-200 border-slate-300 text-slate-400";

    const handleItemChange = (index, field, val) => {
        const newItems = [...items];
        newItems[index][field] = val;
        setItems(newItems);
        onChange(name, newItems);
    };

    const addItem = () => {
        const newItems = [...items, { entity: '', role: roles.length > 0 ? roles[0] : '' }];
        setItems(newItems);
        onChange(name, newItems);
    };

    const removeItem = (index) => {
        const newItems = items.filter((_, i) => i !== index);
        setItems(newItems);
        onChange(name, newItems);
    };

    return (
        <div className={cn(
            "p-4 rounded-2xl border space-y-4",
            darkMode ? "bg-slate-900/50 border-slate-800" : "bg-slate-50 border-slate-200"
        )}>
            {items.length === 0 && (
                <p className="text-base text-slate-500 text-center py-2">No mappings defined</p>
            )}

            {items.map((item, index) => (
                <div key={index} className="flex gap-2 items-start">
                    <input
                        type="text"
                        placeholder="Entity"
                        value={item.entity}
                        disabled={isImmutable}
                        onChange={(e) => handleItemChange(index, 'entity', e.target.value)}
                        className={cn(
                            "flex-1 px-3 h-10 rounded-lg border text-base outline-none transition-all",
                            isImmutable ? disabledBg : inputBg,
                        )}
                    />

                    <select
                        value={item.role}
                        disabled={isImmutable}
                        onChange={(e) => handleItemChange(index, 'role', e.target.value)}
                        className={cn(
                            "w-48 px-2 h-10 rounded-lg border text-base outline-none transition-all",
                            isImmutable ? disabledBg : inputBg,
                        )}
                    >
                        {roles.map(role => (
                            <option key={role} value={role}>{role}</option>
                        ))}
                    </select>

                    {!isImmutable && (
                        <button
                            type="button"
                            onClick={() => removeItem(index)}
                            className="p-2.5 text-rose-500 hover:bg-rose-500/10 rounded-lg transition-colors"
                        >
                            <Trash2 size={18} />
                        </button>
                    )}
                </div>
            ))}

            {!isImmutable && (
                <button
                    type="button"
                    onClick={addItem}
                    className="flex items-center gap-2 text-base font-medium text-blue-500 hover:text-blue-600 transition-colors px-1"
                >
                    <Plus size={16} /> ADD MAPPING
                </button>
            )}
        </div>
    );
};

export default AuthRoleMappingWidget;
