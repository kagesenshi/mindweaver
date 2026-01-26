import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';
import { cn } from '../utils/cn';
import { Save, X, RefreshCcw, AlertCircle, Plus, Trash2 } from 'lucide-react';
import Select from 'react-select';

// Helper sub-component for Key-Value JSON fields
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

const DynamicForm = ({
    entityPath,
    mode = 'create',
    initialData = {},
    onSuccess,
    onCancel,
    darkMode,
    renderExtraActions
}) => {
    const [schema, setSchema] = useState(null);
    const [formData, setFormData] = useState(initialData);
    const [fieldErrors, setFieldErrors] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [relationshipOptions, setRelationshipOptions] = useState({});
    const inputBg = darkMode ? "bg-slate-950 border-slate-800 text-slate-200" : "bg-slate-100 border-slate-200 text-slate-900";
    const disabledBg = darkMode ? "bg-slate-900 border-slate-800 text-slate-500" : "bg-slate-200 border-slate-300 text-slate-400";

    useEffect(() => {
        const fetchSchema = async () => {
            try {
                const viewName = mode === 'create' ? '_create-form' : '_edit-form';
                const response = await apiClient.get(`${entityPath}/${viewName}`);
                const data = response.data.data;
                setSchema(data);

                // Merge initial data with defaults from schema if needed
                if (mode === 'create') {
                    const defaults = {};
                    const properties = data.jsonschema.properties || {};
                    Object.entries(properties).forEach(([key, prop]) => {
                        // Check for jsonschema default
                        if (prop.default !== undefined) {
                            defaults[key] = prop.default;
                        }
                        // Check for widget metadata default
                        const widget = data.widgets?.[key];
                        if (widget?.default_value !== undefined) {
                            defaults[key] = widget.default_value;
                        }
                    });
                    setFormData(prev => ({ ...defaults, ...prev }));
                }

                // Fetch relationship options
                if (data.widgets) {
                    const relOptions = {};
                    for (const [key, widget] of Object.entries(data.widgets)) {
                        if (widget.type === 'relationship' && widget.endpoint) {
                            try {
                                let url = widget.endpoint;
                                // Handle potential double prefixing
                                if (url.startsWith('/api/v1')) {
                                    url = url.substring(7);
                                }

                                console.log(`Fetching options for ${key} from ${url}`);
                                const relResponse = await apiClient.get(url);
                                console.log(`Response for ${key}:`, relResponse.data);

                                let items = [];
                                if (Array.isArray(relResponse.data)) {
                                    items = relResponse.data;
                                } else if (relResponse.data.data) {
                                    items = relResponse.data.data;
                                } else if (relResponse.data.records) {
                                    items = relResponse.data.records;
                                }

                                relOptions[key] = items;
                            } catch (err) {
                                console.error(`Failed to fetch options for ${key}:`, err);
                            }
                        }
                    }
                    setRelationshipOptions(relOptions);
                }

            } catch (err) {
                console.error('Failed to fetch schema:', err);
                setError('Failed to load form schema');
            } finally {
                setLoading(false);
            }
        };

        fetchSchema();
    }, [entityPath, mode, initialData]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        setFieldErrors({});

        // Clean up data before sending (e.g. converting string numbers back to numbers if needed)
        const cleanData = { ...formData };
        if (schema) {
            Object.entries(schema.jsonschema.properties || {}).forEach(([key, prop]) => {
                if (prop.type === 'integer' && cleanData[key] !== undefined && cleanData[key] !== null) {
                    cleanData[key] = parseInt(cleanData[key], 10);
                }
                if (prop.type === 'number' && cleanData[key] !== undefined && cleanData[key] !== null) {
                    cleanData[key] = parseFloat(cleanData[key]);
                }
            });
        }

        try {
            const response = mode === 'create'
                ? await apiClient.post(entityPath, cleanData)
                : await apiClient.put(`${entityPath}/${initialData.id}`, cleanData);

            if (onSuccess) await onSuccess(response.data);
        } catch (err) {
            console.error('Form submission failed:', err);
            const detail = err.response?.data?.detail;
            if (detail) {
                const errors = {};
                const details = Array.isArray(detail) ? detail : [detail];

                details.forEach(err => {
                    if (err.loc && Array.isArray(err.loc)) {
                        let pathParts = err.loc;
                        // Skip request parts
                        if (['body', 'query', 'header'].includes(pathParts[0])) {
                            pathParts = pathParts.slice(1);
                        }
                        const fieldName = pathParts[pathParts.length - 1];
                        errors[fieldName] = err.msg;
                    }
                });

                if (Object.keys(errors).length > 0) {
                    setFieldErrors(errors);
                    setError('Please fix the errors below.');
                } else {
                    setError(err.response?.data?.detail?.msg || err.message || 'Submission failed');
                }
            } else {
                setError(err.message || 'Submission failed');
            }
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (name, value) => {
        setFieldErrors(prev => {
            const next = { ...prev };
            delete next[name];
            return next;
        });
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    if (loading) {
        return (
            <div className="p-12 flex flex-col items-center justify-center space-y-4">
                <RefreshCcw className="animate-spin text-blue-500" size={32} />
                <p className="text-slate-500 text-base font-medium">Loading form configuration...</p>
            </div>
        );
    }

    if (!schema) return null;

    // Filter out internal fields
    const internalFields = schema.internal_fields || [];
    const properties = Object.entries(schema.jsonschema.properties || {})
        .filter(([key]) => !internalFields.includes(key))
        .sort(([keyA], [keyB]) => {
            const orderA = schema.widgets?.[keyA]?.order ?? 999;
            const orderB = schema.widgets?.[keyB]?.order ?? 999;
            return orderA - orderB;
        });


    const renderField = (name, prop, widget) => {
        const hasError = !!fieldErrors[name];
        const label = widget.label || prop.title || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
        // If editing and field is immutable, disable it
        const isImmutable = mode === 'edit' && (schema.immutable_fields || []).includes(name);

        const customStyles = {
            control: (base, state) => ({
                ...base,
                background: state.isDisabled
                    ? (darkMode ? '#0f172a' : '#e2e8f0') // slate-900 : slate-200
                    : (darkMode ? '#020617' : '#f1f5f9'), // slate-950 : slate-100
                borderColor: state.isDisabled
                    ? (darkMode ? '#1e293b' : '#cbd5e1') // slate-800 : slate-300
                    : (hasError ? '#f43f5e' : (darkMode ? '#1e293b' : '#e2e8f0')), // rose-500 : slate-800 : slate-200
                color: state.isDisabled
                    ? (darkMode ? '#64748b' : '#94a3b8') // slate-500 : slate-400
                    : (darkMode ? '#e2e8f0' : '#0f172a'),
                minHeight: '50px',
                borderRadius: '0.75rem',
                boxShadow: state.isFocused ? '0 0 0 1px rgba(59, 130, 246, 0.5)' : 'none',
                opacity: state.isDisabled ? 0.8 : 1,
                cursor: state.isDisabled ? 'not-allowed' : 'default',
                '&:hover': {
                    borderColor: state.isDisabled
                        ? (darkMode ? '#1e293b' : '#cbd5e1')
                        : (darkMode ? '#334155' : '#cbd5e1')
                }
            }),
            menu: (base) => ({
                ...base,
                background: darkMode ? '#020617' : '#ffffff',
                border: `1px solid ${darkMode ? '#1e293b' : '#e2e8f0'}`,
                zIndex: 100
            }),
            option: (base, state) => ({
                ...base,
                backgroundColor: state.isFocused
                    ? (darkMode ? '#1e293b' : '#e2e8f0')
                    : (state.isSelected ? (darkMode ? '#3b82f6' : '#bfdbfe') : 'transparent'),
                color: state.isSelected && darkMode ? '#ffffff' : (darkMode ? '#e2e8f0' : '#0f172a'),
                cursor: 'pointer'
            }),
            singleValue: (base, state) => ({
                ...base,
                color: state.isDisabled
                    ? (darkMode ? '#64748b' : '#94a3b8')
                    : (darkMode ? '#e2e8f0' : '#0f172a'),
            }),
            multiValue: (base) => ({
                ...base,
                backgroundColor: darkMode ? '#1e293b' : '#e2e8f0',
            }),
            multiValueLabel: (base) => ({
                ...base,
                color: darkMode ? '#e2e8f0' : '#0f172a',
            }),
            input: (base) => ({
                ...base,
                color: darkMode ? '#e2e8f0' : '#0f172a',
            })
        };

        // -- Widget Type: Relationship --
        if (widget.type === 'relationship') {
            let options = relationshipOptions[name] || [];
            const isMultiselect = widget.multiselect || false;
            const idField = widget.field || 'id';

            // Filter options based on project_id if applicable
            if (name !== 'project_id' && formData.project_id) {
                options = options.filter(opt => {
                    // If the option doesn't have a project_id, show it (global resource?)
                    // Or strict filtering? "available option must be filtered by the current selected project_id"
                    // Usually implies: if option has project_id, it must match. If it doesn't, maybe it's global?
                    // Let's assume strict matching if option has project_id.
                    if (opt.project_id !== undefined && opt.project_id !== null) {
                        // Loose comparison for string/int mismatch
                        return opt.project_id == formData.project_id;
                    }
                    return true;
                });
            }

            const selectOptions = options.map(opt => ({
                label: opt.title || opt.name || opt[idField],
                value: opt[idField]
            }));

            // Find current value object(s)
            let currentValue = null;
            if (isMultiselect) {
                const currentVals = formData[name] || [];
                currentValue = selectOptions.filter(opt => currentVals.includes(opt.value));
            } else {
                const currentVal = formData[name];
                currentValue = selectOptions.find(opt => opt.value === currentVal) || null;
            }

            return (
                <Select
                    isMulti={isMultiselect}
                    value={currentValue}
                    options={selectOptions}
                    onChange={(selected) => {
                        if (isMultiselect) {
                            handleChange(name, selected ? selected.map(opt => opt.value) : []);
                        } else {
                            handleChange(name, selected ? selected.value : null);
                        }
                    }}
                    isDisabled={isImmutable}
                    styles={customStyles}
                    placeholder={`Select ${label.toLowerCase()}...`}
                    classNamePrefix="react-select"
                />
            );
        }

        // -- Widget Type: Select (Enum or Explicit Options) --
        if (prop.enum || (widget.type === 'select' && widget.options)) {
            const options = widget.options || prop.enum.map(e => ({ label: e, value: e }));
            // Normalize options to { label, value } format
            const selectOptions = options.map(opt => {
                if (typeof opt === 'object') {
                    return { label: opt.label, value: opt.value };
                }
                return { label: opt, value: opt };
            });

            const currentVal = formData[name];
            const currentValue = selectOptions.find(opt => opt.value === currentVal) || null;

            return (
                <Select
                    value={currentValue}
                    options={selectOptions}
                    onChange={(selected) => handleChange(name, selected ? selected.value : null)}
                    isDisabled={isImmutable}
                    styles={customStyles}
                    placeholder={`Select ${label.toLowerCase()}...`}
                    classNamePrefix="react-select"
                />
            );
        }

        // -- Widget Type: Range --
        if (widget.type === 'range') {
            const min = widget.min ?? 0;
            const max = widget.max ?? 100;
            const step = widget.step ?? 1;
            const val = formData[name] ?? min;
            const percentage = ((val - min) / (max - min)) * 100;

            // Generate step markers if number of steps is reasonable
            const numSteps = Math.floor((max - min) / step);
            const showSteps = numSteps > 0 && numSteps <= 15;
            const steps = showSteps ? Array.from({ length: numSteps + 1 }, (_, i) => min + (i * step)) : [];

            return (
                <div className="space-y-2">
                    <div className="mw-range-container">
                        <div
                            className="mw-range-badge"
                            style={{ left: `${percentage}%` }}
                        >
                            {val}
                        </div>
                        <input
                            type="range"
                            min={min}
                            max={max}
                            step={step}
                            value={val}
                            disabled={isImmutable}
                            onChange={(e) => handleChange(name, parseFloat(e.target.value))}
                            className={cn(
                                "mw-range",
                                isImmutable && "cursor-not-allowed opacity-60 grayscale-[0.5]"
                            )}
                            style={{
                                background: isImmutable
                                    ? (darkMode ? '#1e293b' : '#e2e8f0')
                                    : `linear-gradient(to right, #2563eb 0%, #2563eb ${percentage}%, ${darkMode ? '#1e293b' : '#e2e8f0'} ${percentage}%, ${darkMode ? '#1e293b' : '#e2e8f0'} 100%)`
                            }}
                        />
                        {showSteps && (
                            <div className="mw-range-steps">
                                {steps.map((s, i) => (
                                    <div
                                        key={i}
                                        className={cn(
                                            "mw-range-step",
                                            val >= s ? "mw-range-step-active" : ""
                                        )}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        // -- Widget Type: Key-Value --
        if (widget.type === 'key-value') {
            return (
                <KeyValueWidget
                    name={name}
                    value={formData[name]}
                    onChange={handleChange}
                    darkMode={darkMode}
                    isImmutable={isImmutable}
                />
            );
        }

        // -- Widget Type: Boolean --
        if (prop.type === 'boolean') {
            return (
                <div className={cn(
                    "flex items-center gap-3 px-4 h-[50px] rounded-xl border cursor-pointer select-none transition-all",
                    isImmutable ? (darkMode ? "bg-slate-900 border-slate-800" : "bg-slate-200 border-slate-300") : (formData[name] ? "border-blue-500/50 bg-blue-500/5" : inputBg),
                    hasError && "border-rose-500 ring-1 ring-rose-500/50",
                    isImmutable && "cursor-not-allowed opacity-80"
                )} onClick={() => !isImmutable && handleChange(name, !formData[name])}>
                    <div className={cn(
                        "w-10 h-6 rounded-full relative transition-colors p-1",
                        formData[name] ? (isImmutable ? "bg-blue-600/50" : "bg-blue-600") : (isImmutable ? "bg-slate-800" : "bg-slate-700")
                    )}>
                        <div className={cn(
                            "w-4 h-4 bg-white rounded-full transition-transform",
                            formData[name] ? "translate-x-4" : "translate-x-0",
                            isImmutable && "opacity-60"
                        )} />
                    </div>
                    <span className={cn(
                        "text-base font-medium",
                        isImmutable ? "text-slate-500" : ""
                    )}>{formData[name] ? 'Enabled' : 'Disabled'}</span>
                </div>
            );
        }

        // -- Widget Type: Password --
        if (widget.type === 'password' || prop.format === 'password') {
            return (
                <input
                    type="password"
                    value={formData[name] ?? ''}
                    disabled={isImmutable}
                    onChange={(e) => handleChange(name, e.target.value)}
                    placeholder={`Enter ${label.toLowerCase()}...`}
                    className={cn(
                        "w-full px-4 h-[50px] rounded-xl border text-base outline-none focus:ring-2 focus:ring-blue-500/20 transition-all",
                        isImmutable ? disabledBg : inputBg,
                        isImmutable && "cursor-not-allowed opacity-80",
                        hasError && "border-rose-500 ring-1 ring-rose-500/50"
                    )}
                />
            );
        }

        // -- Implicit Textareas (Description, Config, etc) --
        const isTextArea =
            name.includes('description') ||
            name.includes('config') ||
            name.includes('prompt') ||
            name.includes('sql');

        if (isTextArea) {
            const rows = name.includes('description') ? 3 : 5;
            return (
                <textarea
                    value={formData[name] ?? ''}
                    disabled={isImmutable}
                    onChange={(e) => handleChange(name, e.target.value)}
                    placeholder={`Enter ${label.toLowerCase()}...`}
                    rows={rows}
                    className={cn(
                        "w-full px-4 py-3 rounded-xl border text-base outline-none focus:ring-2 focus:ring-blue-500/20 transition-all",
                        isImmutable ? disabledBg : inputBg,
                        isImmutable && "cursor-not-allowed opacity-80",
                        hasError && "border-rose-500 ring-1 ring-rose-500/50"
                    )}
                />
            );
        }

        // -- Default Text/Number Input --
        const isNumeric =
            prop.type === 'integer' ||
            prop.type === 'number' ||
            widget.type === 'integer' ||
            widget.type === 'number' ||
            // Handle anyOf for optional integers in JSON schema
            (prop.anyOf && prop.anyOf.some(a => a.type === 'integer' || a.type === 'number'));

        const isFloat =
            prop.type === 'number' ||
            widget.type === 'number' ||
            (prop.anyOf && prop.anyOf.some(a => a.type === 'number'));

        return (
            <input
                type={isNumeric ? 'number' : 'text'}
                step={isFloat ? 'any' : undefined}
                value={formData[name] ?? ''}
                disabled={isImmutable}
                onChange={(e) => {
                    let val = e.target.value;
                    // Don't convert immediately to allow typing decimals/negatives, convert on submit
                    handleChange(name, val);
                }}
                placeholder={`Enter ${label.toLowerCase()}...`}
                className={cn(
                    "w-full px-4 h-[50px] rounded-xl border text-base outline-none focus:ring-2 focus:ring-blue-500/20 transition-all",
                    isImmutable ? disabledBg : inputBg,
                    isImmutable && "cursor-not-allowed opacity-80",
                    hasError && "border-rose-500 ring-1 ring-rose-500/50"
                )}
            />
        );
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3 text-rose-500 text-base">
                    <AlertCircle size={18} />
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {properties.map(([name, prop]) => {
                    const widget = schema.widgets?.[name] || {};
                    // Use column_span from metadata, default to 1 (unless implicit rules exist)
                    // Flutter default is 2 (full width) unless specified? 
                    // Let's stick to explicit span or 2 (full) for major fields, 1 for small?
                    // Actually Flutter implementation defaults to span 2 (full width) if null.
                    // Wait, line 145 of usage: final span = field.metadata?.columnSpan ?? 2;
                    // So default is FULL WIDTH in Flutter.
                    const colSpan = widget.column_span ?? 2;
                    const isFullWidth = colSpan === 2;

                    const label = widget.label || prop.title || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
                    const hasError = !!fieldErrors[name];

                    return (
                        <div key={name} className={cn(
                            "space-y-2",
                            isFullWidth ? "md:col-span-2" : "md:col-span-1"
                        )}>
                            <label className={cn(
                                "mw-label",
                                hasError ? "text-rose-500" : ""
                            )}>
                                {label} {prop.required ? '*' : ''}
                            </label>

                            {renderField(name, prop, widget)}

                            {hasError && (
                                <p className="text-sm text-rose-500 px-1 font-medium">{fieldErrors[name]}</p>
                            )}
                            {prop.description && (
                                <p className="text-sm text-slate-500 px-1 italic">{prop.description}</p>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="flex items-center gap-4 pt-4">
                <button
                    type="submit"
                    disabled={saving}
                    className="mw-btn-primary flex-1 py-4"
                >
                    {saving ? <RefreshCcw size={18} className="animate-spin" /> : <Save size={18} />}
                    {saving ? 'SAVING CHANGES...' : (mode === 'create' ? 'CREATE RESOURCE' : 'SAVE CHANGES')}
                </button>
                {renderExtraActions && renderExtraActions(formData)}
                {onCancel && (
                    <button
                        type="button"
                        onClick={onCancel}
                        className="mw-btn-secondary px-8 py-4"
                    >
                        <X size={18} /> CANCEL
                    </button>
                )}
            </div>
        </form >
    );
};

export default DynamicForm;
