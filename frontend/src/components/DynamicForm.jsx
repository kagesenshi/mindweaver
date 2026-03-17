import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';
import { cn } from '../utils/cn';
import { Save, X, RefreshCcw, AlertCircle } from 'lucide-react';
import KeyValueWidget from './form_widgets/KeyValueWidget';
import AuthRoleMappingWidget from './form_widgets/AuthRoleMappingWidget';
import RelationshipWidget from './form_widgets/RelationshipWidget';
import SelectWidget from './form_widgets/SelectWidget';
import RangeWidget from './form_widgets/RangeWidget';
import BooleanWidget from './form_widgets/BooleanWidget';
import PasswordWidget from './form_widgets/PasswordWidget';
import TextAreaWidget from './form_widgets/TextAreaWidget';
import InputWidget from './form_widgets/InputWidget';



const DynamicForm = ({
    entityPath,
    mode = 'create',
    initialData = {},
    onSuccess,
    onCancel,
    darkMode,
    renderExtraActions
}) => {
    // Note: initialData is used as the basis for initial state, but shouldn't trigger
    // a re-fetch of the schema itself. The schema is determined by entityPath and mode.
    const [schema, setSchema] = useState(null);
    const [formData, setFormData] = useState(initialData);
    const [fieldErrors, setFieldErrors] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [relationshipOptions, setRelationshipOptions] = useState({});
    const [selectEndpointOptions, setSelectEndpointOptions] = useState({});
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

                    // Fetch dynamic select options (type: 'select' with endpoint)
                    const selOptions = {};
                    for (const [key, widget] of Object.entries(data.widgets)) {
                        if (widget.type === 'select' && widget.endpoint) {
                            try {
                                let url = widget.endpoint;
                                if (url.startsWith('/api/v1')) {
                                    url = url.substring(7);
                                }
                                const selResponse = await apiClient.get(url);
                                let items = [];
                                if (Array.isArray(selResponse.data)) {
                                    items = selResponse.data;
                                } else if (selResponse.data?.data) {
                                    items = selResponse.data.data;
                                }
                                // Normalise to { label, value }
                                selOptions[key] = items.map(item =>
                                    typeof item === 'object' ? item : { label: item, value: item }
                                );
                            } catch (err) {
                                console.error(`Failed to fetch select options for ${key}:`, err);
                            }
                        }
                    }
                    setSelectEndpointOptions(selOptions);
                }

            } catch (err) {
                console.error('Failed to fetch schema:', err);
                setError('Failed to load form schema');
            } finally {
                setLoading(false);
            }
        };

        fetchSchema();
    }, [entityPath, mode]); // Removed initialData from dependencies to prevent infinite loop

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        setFieldErrors({});

        // Clean up data before sending (e.g. converting string numbers back to numbers if needed)
        const cleanData = { ...formData };
        if (schema) {
            const getEffectiveType = (p) => {
                if (p.type) return p.type;
                if (p.anyOf) {
                    const types = p.anyOf.map(a => a.type).filter(t => t && t !== 'null');
                    if (types.length === 1) return types[0];
                }
                return null;
            };

            Object.entries(schema.jsonschema.properties || {}).forEach(([key, prop]) => {
                const effectiveType = getEffectiveType(prop);
                if (effectiveType === 'integer' && cleanData[key] !== undefined && cleanData[key] !== null) {
                    cleanData[key] = parseInt(cleanData[key], 10);
                }
                if (effectiveType === 'number' && cleanData[key] !== undefined && cleanData[key] !== null) {
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

        const getEffectiveType = (p) => {
            if (p.type) return p.type;
            if (p.anyOf) {
                const types = p.anyOf.map(a => a.type).filter(t => t && t !== 'null');
                if (types.length === 1) return types[0];
            }
            return null;
        };

        const effectiveType = getEffectiveType(prop);

        // -- Widget Type: Relationship --
        if (widget.type === 'relationship') {
            return (
                <RelationshipWidget
                    name={name}
                    label={label}
                    widget={widget}
                    formData={formData}
                    relationshipOptions={relationshipOptions}
                    onChange={handleChange}
                    darkMode={darkMode}
                    isImmutable={isImmutable}
                    hasError={hasError}
                />
            );
        }

        // -- Widget Type: Select (Enum or Explicit Options) --
        if (prop.enum || (widget.type === 'select' && (widget.options || widget.endpoint))) {
            return (
                <SelectWidget
                    name={name}
                    label={label}
                    prop={prop}
                    widget={widget}
                    formData={formData}
                    selectEndpointOptions={selectEndpointOptions}
                    onChange={handleChange}
                    darkMode={darkMode}
                    isImmutable={isImmutable}
                    hasError={hasError}
                />
            );
        }

        // -- Widget Type: Range --
        if (widget.type === 'range') {
            return (
                <RangeWidget
                    name={name}
                    widget={widget}
                    formData={formData}
                    onChange={handleChange}
                    darkMode={darkMode}
                    isImmutable={isImmutable}
                />
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

        // -- Widget Type: Auth-Role Mapping --
        if (widget.type === 'auth-role-mapping') {
            return (
                <AuthRoleMappingWidget
                    name={name}
                    value={formData[name]}
                    roles={widget.roles}
                    onChange={handleChange}
                    darkMode={darkMode}
                    isImmutable={isImmutable}
                />
            );
        }

        // -- Widget Type: Boolean --
        if (effectiveType === 'boolean') {
            return (
                <BooleanWidget
                    name={name}
                    formData={formData}
                    onChange={handleChange}
                    darkMode={darkMode}
                    isImmutable={isImmutable}
                    hasError={hasError}
                    inputBg={inputBg}
                />
            );
        }

        // -- Widget Type: Password --
        if (widget.type === 'password' || prop.format === 'password') {
            return (
                <PasswordWidget
                    name={name}
                    label={label}
                    widget={widget}
                    formData={formData}
                    onChange={handleChange}
                    isImmutable={isImmutable}
                    disabledBg={disabledBg}
                    inputBg={inputBg}
                    hasError={hasError}
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
            return (
                <TextAreaWidget
                    name={name}
                    label={label}
                    widget={widget}
                    formData={formData}
                    onChange={handleChange}
                    isImmutable={isImmutable}
                    disabledBg={disabledBg}
                    inputBg={inputBg}
                    hasError={hasError}
                />
            );
        }

        // -- Default Text/Number Input --
        return (
            <InputWidget
                name={name}
                label={label}
                widget={widget}
                formData={formData}
                onChange={handleChange}
                isImmutable={isImmutable}
                disabledBg={disabledBg}
                inputBg={inputBg}
                hasError={hasError}
                effectiveType={effectiveType}
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
