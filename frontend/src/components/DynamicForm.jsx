import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';
import { cn } from '../utils/cn';
import { Save, X, RefreshCcw, AlertCircle } from 'lucide-react';

const DynamicForm = ({
    entityPath,
    mode = 'create',
    initialData = {},
    onSuccess,
    onCancel,
    darkMode
}) => {
    const [schema, setSchema] = useState(null);
    const [formData, setFormData] = useState(initialData);
    const [fieldErrors, setFieldErrors] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [relationshipOptions, setRelationshipOptions] = useState({});

    useEffect(() => {
        const fetchSchema = async () => {
            try {
                const viewName = mode === 'create' ? '_create-form' : '_edit-form';
                const response = await apiClient.get(`${entityPath}/${viewName}`);
                const record = response.data.record;
                setSchema(record);

                // Merge initial data with defaults from schema if needed
                if (mode === 'create') {
                    const defaults = {};
                    const properties = record.jsonschema.properties || {};
                    Object.entries(properties).forEach(([key, prop]) => {
                        // Check for jsonschema default
                        if (prop.default !== undefined) {
                            defaults[key] = prop.default;
                        }
                        // Check for widget metadata default
                        const widget = record.widgets?.[key];
                        if (widget?.default_value !== undefined) {
                            defaults[key] = widget.default_value;
                        }
                    });
                    setFormData(prev => ({ ...defaults, ...prev }));
                }

                // Fetch relationship options
                if (record.widgets) {
                    const relOptions = {};
                    for (const [key, widget] of Object.entries(record.widgets)) {
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
                                } else if (relResponse.data.records) {
                                    items = relResponse.data.records;
                                } else if (relResponse.data.data) {
                                    items = relResponse.data.data;
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
    }, [entityPath, mode]);

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

            if (onSuccess) onSuccess(response.data);
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
                <p className="text-slate-500 text-sm font-medium">Loading form configuration...</p>
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

    const inputBg = darkMode ? "bg-slate-950 border-slate-800 text-slate-200" : "bg-slate-100 border-slate-200 text-slate-900";

    const renderField = (name, prop, widget) => {
        const hasError = !!fieldErrors[name];
        const label = widget.label || prop.title || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
        // If editing and field is immutable, disable it
        const isImmutable = mode === 'edit' && (schema.immutable_fields || []).includes(name);

        // -- Widget Type: Relationship --
        if (widget.type === 'relationship') {
            const options = relationshipOptions[name] || [];
            const isMultiselect = widget.multiselect || false;
            const idField = widget.field || 'id';

            // TODO: Implement a better multi-select UI
            return (
                <select
                    multiple={isMultiselect}
                    value={formData[name] || (isMultiselect ? [] : '')}
                    disabled={isImmutable}
                    onChange={(e) => {
                        if (isMultiselect) {
                            const selected = Array.from(e.target.selectedOptions, option => option.value);
                            // Need to convert values to correct type if IDs are numbers?
                            // Assuming IDs are handled as strings for value but backend might want ints
                            // For now keep as strings/mixed
                            handleChange(name, selected);
                        } else {
                            handleChange(name, e.target.value);
                        }
                    }}
                    className={cn(
                        "w-full px-4 py-3 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-all",
                        inputBg,
                        hasError && "border-rose-500 ring-1 ring-rose-500/50",
                        isMultiselect && "h-32"
                    )}
                >
                    {!isMultiselect && <option value="">Select {label.toLowerCase()}...</option>}
                    {options.map(opt => {
                        const val = opt[idField];
                        const title = opt.title || opt.name || val;
                        return <option key={val} value={val}>{title}</option>;
                    })}
                </select>
            );
        }

        // -- Widget Type: Select (Enum or Explicit Options) --
        if (prop.enum || (widget.type === 'select' && widget.options)) {
            const options = widget.options || prop.enum.map(e => ({ label: e, value: e }));
            return (
                <select
                    value={formData[name] || ''}
                    disabled={isImmutable}
                    onChange={(e) => handleChange(name, e.target.value)}
                    className={cn(
                        "w-full px-4 py-3 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-all",
                        inputBg,
                        hasError && "border-rose-500 ring-1 ring-rose-500/50"
                    )}
                >
                    <option value="">Select {label.toLowerCase()}...</option>
                    {options.map(opt => {
                        const val = typeof opt === 'object' ? opt.value : opt;
                        const displayLabel = typeof opt === 'object' ? opt.label : opt;
                        return <option key={val} value={val}>{displayLabel}</option>;
                    })}
                </select>
            );
        }

        // -- Widget Type: Range --
        if (widget.type === 'range') {
            const min = widget.min ?? 0;
            const max = widget.max ?? 100;
            const val = formData[name] ?? min;

            return (
                <div className="space-y-2">
                    <div className="flex justify-between text-xs font-mono opacity-70">
                        <span>{min}</span>
                        <span className="font-bold text-blue-500">{val}</span>
                        <span>{max}</span>
                    </div>
                    <input
                        type="range"
                        min={min}
                        max={max}
                        value={val}
                        disabled={isImmutable}
                        onChange={(e) => handleChange(name, parseFloat(e.target.value))}
                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer dark:bg-slate-700 accent-blue-600"
                    />
                </div>
            );
        }

        // -- Widget Type: Boolean --
        if (prop.type === 'boolean') {
            return (
                <div className={cn(
                    "flex items-center gap-3 p-3 rounded-xl border cursor-pointer select-none transition-all",
                    formData[name] ? "border-blue-500/50 bg-blue-500/5" : inputBg,
                    hasError && "border-rose-500 ring-1 ring-rose-500/50",
                    isImmutable && "opacity-60 cursor-not-allowed"
                )} onClick={() => !isImmutable && handleChange(name, !formData[name])}>
                    <div className={cn(
                        "w-10 h-6 rounded-full relative transition-colors p-1",
                        formData[name] ? "bg-blue-600" : "bg-slate-700"
                    )}>
                        <div className={cn(
                            "w-4 h-4 bg-white rounded-full transition-transform",
                            formData[name] ? "translate-x-4" : "translate-x-0"
                        )} />
                    </div>
                    <span className="text-sm font-medium">{formData[name] ? 'Enabled' : 'Disabled'}</span>
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
                        "w-full px-4 py-3 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-mono",
                        inputBg,
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
                        "w-full px-4 py-3 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-mono",
                        inputBg,
                        hasError && "border-rose-500 ring-1 ring-rose-500/50"
                    )}
                />
            );
        }

        // -- Default Text/Number Input --
        return (
            <input
                type={prop.type === 'integer' || prop.type === 'number' ? 'number' : 'text'}
                step={prop.type === 'number' ? 'any' : undefined}
                value={formData[name] ?? ''}
                disabled={isImmutable}
                onChange={(e) => {
                    let val = e.target.value;
                    // Don't convert immediately to allow typing decimals/negatives, convert on submit
                    handleChange(name, val);
                }}
                placeholder={`Enter ${label.toLowerCase()}...`}
                className={cn(
                    "w-full px-4 py-3 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-mono",
                    inputBg,
                    hasError && "border-rose-500 ring-1 ring-rose-500/50"
                )}
            />
        );
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3 text-rose-500 text-sm">
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
                                "text-[10px] font-bold uppercase tracking-widest px-1 transition-colors",
                                hasError ? "text-rose-500" : "text-slate-500"
                            )}>
                                {label} {prop.required ? '*' : ''}
                            </label>

                            {renderField(name, prop, widget)}

                            {hasError && (
                                <p className="text-[10px] text-rose-500 px-1 font-medium">{fieldErrors[name]}</p>
                            )}
                            {prop.description && (
                                <p className="text-[10px] text-slate-500 px-1 italic">{prop.description}</p>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="flex items-center gap-4 pt-4">
                <button
                    type="submit"
                    disabled={saving}
                    className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white font-bold py-4 rounded-2xl flex items-center justify-center gap-3 transition-all shadow-lg shadow-blue-600/20"
                >
                    {saving ? <RefreshCcw size={18} className="animate-spin" /> : <Save size={18} />}
                    {saving ? 'SAVING CHANGES...' : (mode === 'create' ? 'CREATE RESOURCE' : 'SAVE CHANGES')}
                </button>
                {onCancel && (
                    <button
                        type="button"
                        onClick={onCancel}
                        className={cn(
                            "px-8 py-4 rounded-2xl font-bold flex items-center gap-2 border transition-all",
                            darkMode ? "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                        )}
                    >
                        <X size={18} /> CANCEL
                    </button>
                )}
            </div>
        </form>
    );
};

export default DynamicForm;
