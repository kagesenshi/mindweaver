/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React, { useState } from 'react';
import { cn } from '../../utils/cn';
import { Plus, Trash2 } from 'lucide-react';

/**
 * KeyValueWidget - Helper component for Key-Value JSON fields
 * 
 * @param {string} name - Field name
 * @param {object} value - Initial object value
 * @param {function} onChange - Callback function(name, value)
 * @param {boolean} darkMode - Whether dark mode is enabled
 * @param {boolean} isImmutable - Whether the field is disabled
 */
const KeyValueWidget = ({ name, value, onChange, darkMode, isImmutable }) => {
    // Initial load: convert object to array of items
    const [items, setItems] = useState(() => {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
            return Object.entries(value).map(([k, v]) => {
                let type = 'string';
                if (typeof v === 'number') {
                    type = Number.isInteger(v) ? 'integer' : 'float';
                } else if (typeof v === 'boolean') {
                    type = 'boolean';
                }
                return { key: k, value: v, type };
            });
        }
        return [];
    });

    const inputBg = darkMode ? "bg-slate-950 border-slate-800 text-slate-200" : "bg-slate-100 border-slate-200 text-slate-900";
    const disabledBg = darkMode ? "bg-slate-900 border-slate-800 text-slate-500" : "bg-slate-200 border-slate-300 text-slate-400";

    const handleItemChange = (index, field, val) => {
        const newItems = [...items];
        newItems[index][field] = val;

        // If type changes, try to convert value
        if (field === 'type') {
            const currentVal = newItems[index].value;
            if (val === 'integer') newItems[index].value = parseInt(currentVal) || 0;
            else if (val === 'float') newItems[index].value = parseFloat(currentVal) || 0;
            else if (val === 'boolean') newItems[index].value = (currentVal === 'true' || currentVal === true);
            else newItems[index].value = String(currentVal);
        }

        setItems(newItems);
        syncChanges(newItems);
    };

    const addItem = () => {
        const newItems = [...items, { key: '', value: '', type: 'string' }];
        setItems(newItems);
    };

    const removeItem = (index) => {
        const newItems = items.filter((_, i) => i !== index);
        setItems(newItems);
        syncChanges(newItems);
    };

    const syncChanges = (currentItems) => {
        const obj = {};
        currentItems.forEach(item => {
            if (item.key.trim()) {
                let val = item.value;
                if (item.type === 'integer') val = parseInt(val) || 0;
                else if (item.type === 'float') val = parseFloat(val) || 0;
                else if (item.type === 'boolean') val = (val === 'true' || val === true);
                obj[item.key.trim()] = val;
            }
        });
        onChange(name, obj);
    };

    const typeOptions = [
        { label: 'String', value: 'string' },
        { label: 'Integer', value: 'integer' },
        { label: 'Float', value: 'float' },
        { label: 'Boolean', value: 'boolean' },
    ];

    return (
        <div className={cn(
            "p-4 rounded-2xl border space-y-4",
            darkMode ? "bg-slate-900/50 border-slate-800" : "bg-slate-50 border-slate-200"
        )}>
            {items.length === 0 && (
                <p className="text-base text-slate-500 text-center py-2">No parameters defined</p>
            )}

            {items.map((item, index) => (
                <div key={index} className="flex gap-2 items-start">
                    <input
                        type="text"
                        placeholder="Key"
                        value={item.key}
                        disabled={isImmutable}
                        onChange={(e) => handleItemChange(index, 'key', e.target.value)}
                        className={cn(
                            "flex-1 px-3 h-10 rounded-lg border text-base outline-none transition-all",
                            isImmutable ? disabledBg : inputBg,
                            isImmutable && "cursor-not-allowed opacity-80"
                        )}
                    />

                    <select
                        value={item.type}
                        disabled={isImmutable}
                        onChange={(e) => handleItemChange(index, 'type', e.target.value)}
                        className={cn(
                            "w-28 px-2 h-10 rounded-lg border text-base outline-none transition-all",
                            isImmutable ? disabledBg : inputBg,
                            isImmutable && "cursor-not-allowed opacity-80"
                        )}
                    >
                        {typeOptions.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>

                    {item.type === 'boolean' ? (
                        <select
                            value={item.value ? 'true' : 'false'}
                            disabled={isImmutable}
                            onChange={(e) => handleItemChange(index, 'value', e.target.value === 'true')}
                            className={cn(
                                "flex-1 px-3 h-10 rounded-lg border text-base outline-none transition-all",
                                isImmutable ? disabledBg : inputBg,
                                isImmutable && "cursor-not-allowed opacity-80"
                            )}
                        >
                            <option value="true">True</option>
                            <option value="false">False</option>
                        </select>
                    ) : (
                        <input
                            type={item.type === 'integer' || item.type === 'float' ? 'number' : 'text'}
                            step={item.type === 'float' ? 'any' : undefined}
                            placeholder="Value"
                            value={item.value}
                            disabled={isImmutable}
                            onChange={(e) => handleItemChange(index, 'value', e.target.value)}
                            className={cn(
                                "flex-1 px-3 h-10 rounded-lg border text-base outline-none transition-all",
                                isImmutable ? disabledBg : inputBg,
                                isImmutable && "cursor-not-allowed opacity-80"
                            )}
                        />
                    )}

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
                    <Plus size={16} /> ADD PARAMETER
                </button>
            )}
        </div>
    );
};

export default KeyValueWidget;
