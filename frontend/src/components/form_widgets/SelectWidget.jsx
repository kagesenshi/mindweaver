/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React from 'react';
import Select from 'react-select';
import { getSelectStyles } from './widgetStyles';

/**
 * SelectWidget - Component for dropdown selection (enum or explicit options)
 */
const SelectWidget = ({
    name,
    label,
    prop,
    widget,
    formData,
    selectEndpointOptions,
    onChange,
    darkMode,
    isImmutable,
    hasError,
    required
}) => {
    const staticOpts = widget.options || prop.enum?.map(e => ({ label: e, value: e })) || [];
    // Use dynamically-fetched endpoint options when available, else fall back to static
    const options = (widget.endpoint && selectEndpointOptions[name]?.length > 0)
        ? selectEndpointOptions[name]
        : staticOpts;
        
    // Normalize options to { label, value } format
    const selectOptions = Array.isArray(options) ? options.map(opt => {
        if (typeof opt === 'object') {
            return { label: opt.label, value: opt.value };
        }
        return { label: opt, value: opt };
    }) : [];

    const currentVal = formData[name];
    const currentValue = selectOptions.find(opt => opt.value === currentVal) || null;

    return (
        <Select
            value={currentValue}
            options={selectOptions}
            onChange={(selected) => onChange(name, selected ? selected.value : null)}
            isDisabled={isImmutable}
            isClearable={!required}
            styles={getSelectStyles(darkMode, hasError)}
            placeholder={widget.placeholder || `Select ${label.toLowerCase()}...`}
            classNamePrefix="react-select"
        />
    );
};

export default SelectWidget;
