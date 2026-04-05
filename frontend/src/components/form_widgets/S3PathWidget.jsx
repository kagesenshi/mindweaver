/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React, { useState, useEffect, useRef } from 'react';
import Select from 'react-select';
import { getSelectStyles } from './widgetStyles';
import apiClient from '../../services/api';
import { cn } from '../../utils/cn';
import { Folder, Loader2 } from 'lucide-react';

/**
 * S3PathWidget - Compound widget for selecting S3 bucket and path prefix
 * with autocomplete suggestions from the actual S3 storage.
 */
const S3PathWidget = ({
    name,
    label,
    widget,
    formData,
    onChange,
    darkMode,
    isImmutable,
    hasError,
    required
}) => {
    const storageField = widget.storage_field || 's3_storage_id';
    const storageId = formData[storageField];
    const currentValue = formData[name] || 's3://ranger/audit';

    // Parse current URI: s3://bucket/path
    const parseUri = (uri) => {
        if (!uri || !uri.startsWith('s3://')) return { bucket: '', path: '' };
        const parts = uri.substring(5).split('/');
        const bucket = parts[0];
        const path = parts.slice(1).join('/');
        return { bucket, path };
    };

    const { bucket: initialBucket, path: initialPath } = parseUri(currentValue);
    const [bucket, setBucket] = useState(initialBucket);
    const [path, setPath] = useState(initialPath);
    const [buckets, setBuckets] = useState([]);
    const [loadingBuckets, setLoadingBuckets] = useState(false);
    const [suggestions, setSuggestions] = useState([]);
    const [loadingSuggestions, setLoadingSuggestions] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);

    const suggestionRef = useRef(null);

    // Update internal state when external value changes (e.g. initial load)
    useEffect(() => {
        const { bucket: b, path: p } = parseUri(currentValue);
        setBucket(b);
        setPath(p);
    }, [currentValue]);

    // Fetch buckets when storage changes
    useEffect(() => {
        if (!storageId) {
            setBuckets([]);
            return;
        }

        const fetchBuckets = async () => {
            setLoadingBuckets(true);
            try {
                const response = await apiClient.get(`/s3_storages/${storageId}/_fs?action=ls`);
                const items = response.data.items || [];
                setBuckets(items.map(b => ({ label: b.name, value: b.name })));
            } catch (err) {
                console.error("Failed to fetch buckets", err);
                setBuckets([]);
            } finally {
                setLoadingBuckets(false);
            }
        };

        fetchBuckets();
    }, [storageId]);

    // Fetch path suggestions when bucket or path changes
    useEffect(() => {
        if (!storageId || !bucket || !showSuggestions) {
            setSuggestions([]);
            return;
        }

        const timer = setTimeout(async () => {
            setLoadingSuggestions(true);
            try {
                // We want to list directories with the current path as prefix
                const response = await apiClient.get(`/s3_storages/${storageId}/_fs?action=ls&bucket=${bucket}&prefix=${path}`);
                const items = response.data.items || [];
                setSuggestions(items.filter(i => i.type === 'directory'));
            } catch (err) {
                console.error("Failed to fetch suggestions", err);
                setSuggestions([]);
            } finally {
                setLoadingSuggestions(false);
            }
        }, 500); // 500ms debounce

        return () => clearTimeout(timer);
    }, [storageId, bucket, path, showSuggestions]);

    const handleUpdate = (newBucket, newPath) => {
        let cleanPath = newPath;
        if (cleanPath.startsWith('/')) cleanPath = cleanPath.substring(1);
        const uri = `s3://${newBucket}/${cleanPath}`;
        onChange(name, uri);
    };

    const handleBucketChange = (selected) => {
        const newBucket = selected ? selected.value : '';
        setBucket(newBucket);
        handleUpdate(newBucket, path);
    };

    const handlePathChange = (e) => {
        const newPath = e.target.value;
        setPath(newPath);
        setShowSuggestions(true);
        handleUpdate(bucket, newPath);
    };

    const handleSelectSuggestion = (suggestion) => {
        setPath(suggestion.path);
        setShowSuggestions(false);
        handleUpdate(bucket, suggestion.path);
    };

    // Close suggestions on click outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (suggestionRef.current && !suggestionRef.current.contains(event.target)) {
                setShowSuggestions(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const inputBg = darkMode ? "bg-slate-950 border-slate-800 text-slate-200" : "bg-slate-100 border-slate-200 text-slate-900";

    return (
        <div className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Bucket Dropdown */}
                <div className="md:col-span-1">
                    <Select
                        isLoading={loadingBuckets}
                        options={buckets}
                        value={buckets.find(b => b.value === bucket) || (bucket ? { label: bucket, value: bucket } : null)}
                        onChange={handleBucketChange}
                        isDisabled={isImmutable || !storageId}
                        styles={getSelectStyles(darkMode, hasError)}
                        placeholder="Select Bucket..."
                        classNamePrefix="react-select"
                    />
                </div>

                {/* Path Input with Autocomplete */}
                <div className="md:col-span-2 relative" ref={suggestionRef}>
                    <div className="relative">
                        <input
                            type="text"
                            value={path}
                            onChange={handlePathChange}
                            onFocus={() => setShowSuggestions(true)}
                            disabled={isImmutable || !bucket}
                            placeholder="Enter path prefix (e.g. audit/logs/)"
                            className={cn(
                                "w-full px-4 h-[50px] rounded-xl border text-base outline-none focus:ring-2 focus:ring-blue-500/20 transition-all",
                                (isImmutable || !bucket) ? (darkMode ? "bg-slate-900 border-slate-800 text-slate-500" : "bg-slate-200 border-slate-300 text-slate-400") : inputBg,
                                hasError && "border-rose-500 ring-1 ring-rose-500/50"
                            )}
                        />
                        {loadingSuggestions && (
                            <div className="absolute right-4 top-1/2 -translate-y-1/2">
                                <Loader2 size={16} className="animate-spin text-blue-500" />
                            </div>
                        )}
                    </div>

                    {showSuggestions && suggestions.length > 0 && (
                        <div className={cn(
                            "absolute left-0 right-0 top-[55px] z-[110] border rounded-xl overflow-hidden shadow-xl max-h-60 overflow-y-auto",
                            darkMode ? "bg-slate-950 border-slate-800" : "bg-white border-slate-200 shadow-2xl"
                        )}>
                            {suggestions.map((s, i) => (
                                <button
                                    key={i}
                                    type="button"
                                    onClick={() => handleSelectSuggestion(s)}
                                    className={cn(
                                        "w-full px-4 py-3 flex items-center gap-3 text-sm transition-colors text-left",
                                        darkMode ? "hover:bg-slate-800 text-slate-300 border-b border-slate-900" : "hover:bg-slate-50 text-slate-600 border-b border-slate-50"
                                    )}
                                >
                                    <Folder size={14} className="text-amber-500 shrink-0" />
                                    <span className="truncate">{s.path}</span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
            {!storageId && (
                <p className="text-xs text-rose-500/70 italic px-1">Please select an S3 Storage first.</p>
            )}
        </div>
    );
};

export default S3PathWidget;
