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
                        if (prop.default !== undefined) defaults[key] = prop.default;
                    });
                    setFormData(prev => ({ ...defaults, ...prev }));
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
        try {
            const response = mode === 'create'
                ? await apiClient.post(entityPath, formData)
                : await apiClient.put(`${entityPath}/${initialData.id}`, formData);

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

    // Sort properties by order metadata
    const properties = Object.entries(schema.jsonschema.properties || {})
        .sort(([keyA], [keyB]) => (schema.widgets?.[keyA]?.order || 999) - (schema.widgets?.[keyB]?.order || 999));

    const inputBg = darkMode ? "bg-slate-950 border-slate-800 text-slate-200" : "bg-slate-100 border-slate-200 text-slate-900";

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
                    const isFullWidth = widget.column_span === 2;
                    const label = widget.label || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
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

                            {prop.type === 'boolean' ? (
                                <div className={cn(
                                    "flex items-center gap-3 p-3 rounded-xl border cursor-pointer select-none transition-all",
                                    formData[name] ? "border-blue-500/50 bg-blue-500/5" : inputBg,
                                    hasError && "border-rose-500 ring-1 ring-rose-500/50"
                                )} onClick={() => handleChange(name, !formData[name])}>
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
                            ) : (prop.enum || widget.options) ? (
                                <select
                                    value={formData[name] || ''}
                                    onChange={(e) => handleChange(name, e.target.value)}
                                    className={cn(
                                        "w-full px-4 py-3 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-all",
                                        inputBg,
                                        hasError && "border-rose-500 ring-1 ring-rose-500/50"
                                    )}
                                >
                                    <option value="">Select {label.toLowerCase()}...</option>
                                    {(widget.options || prop.enum).map(opt => {
                                        const value = typeof opt === 'object' ? opt.value : opt;
                                        const displayLabel = typeof opt === 'object' ? opt.label : opt;
                                        return <option key={value} value={value}>{displayLabel}</option>;
                                    })}
                                </select>
                            ) : (
                                <input
                                    type={prop.format === 'password' ? 'password' : (prop.type === 'integer' ? 'number' : 'text')}
                                    value={formData[name] ?? ''}
                                    onChange={(e) => {
                                        let val = e.target.value;
                                        if (prop.type === 'integer') {
                                            val = val === '' ? undefined : parseInt(val);
                                        }
                                        handleChange(name, val);
                                    }}
                                    placeholder={`Enter ${label.toLowerCase()}...`}
                                    className={cn(
                                        "w-full px-4 py-3 rounded-xl border text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-all font-mono",
                                        inputBg,
                                        hasError && "border-rose-500 ring-1 ring-rose-500/50"
                                    )}
                                />
                            )}
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
