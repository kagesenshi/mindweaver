/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React from 'react';
import Select from 'react-select';
import { getSelectStyles } from './widgetStyles';

/**
 * RelationshipWidget - Component for selecting related resources
 */
const RelationshipWidget = React.memo(({ 
    name, 
    label, 
    widget, 
    value,
    projectId, 
    relationshipOptions, 
    onChange, 
    darkMode, 
    isImmutable, 
    hasError,
    required
}) => {
    let options = relationshipOptions[name] || [];
    const isMultiselect = widget.multiselect || false;
    const idField = widget.field || 'id';

    // Filter options based on project_id if applicable
    if (name !== 'project_id' && projectId) {
        options = options.filter(opt => {
            if (opt.project_id !== undefined && opt.project_id !== null) {
                return opt.project_id == projectId;
            }
            return true;
        });
    }

    const selectOptions = Array.isArray(options) ? options.map(opt => ({
        label: opt.title || opt.name || opt[idField],
        value: opt[idField]
    })) : [];

    // Find current value object(s)
    let currentValue = null;
    if (isMultiselect) {
        const currentVals = value || [];
        currentValue = selectOptions.filter(opt => currentVals.includes(opt.value));
    } else {
        currentValue = selectOptions.find(opt => opt.value === value) || null;
    }

    return (
        <Select
            isMulti={isMultiselect}
            value={currentValue}
            options={selectOptions}
            onChange={(selected) => {
                if (isMultiselect) {
                    onChange(name, selected ? selected.map(opt => opt.value) : []);
                } else {
                    onChange(name, selected ? selected.value : null);
                }
            }}
            isDisabled={isImmutable}
            isClearable={!required}
            styles={getSelectStyles(darkMode, hasError)}
            placeholder={widget.placeholder || `Select ${label.toLowerCase()}...`}
            classNamePrefix="react-select"
        />
    );
});

RelationshipWidget.displayName = 'RelationshipWidget';

export default RelationshipWidget;
