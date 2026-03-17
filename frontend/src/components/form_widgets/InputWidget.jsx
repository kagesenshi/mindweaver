/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React from 'react';
import { cn } from '../../utils/cn';

/**
 * InputWidget - Default text or number input
 */
const InputWidget = ({ 
    name, 
    label, 
    widget, 
    formData, 
    onChange, 
    isImmutable, 
    disabledBg, 
    inputBg, 
    hasError,
    effectiveType
}) => {
    const isNumeric =
        effectiveType === 'integer' ||
        effectiveType === 'number' ||
        widget.type === 'integer' ||
        widget.type === 'number';

    const isFloat =
        effectiveType === 'number' ||
        widget.type === 'number';

    return (
        <input
            type={isNumeric ? 'number' : 'text'}
            step={isFloat ? 'any' : undefined}
            value={formData[name] ?? ''}
            disabled={isImmutable}
            onChange={(e) => {
                let val = e.target.value;
                // Don't convert immediately to allow typing decimals/negatives, convert on submit
                onChange(name, val);
            }}
            placeholder={widget.placeholder || `Enter ${label.toLowerCase()}...`}
            className={cn(
                "w-full px-4 h-[50px] rounded-xl border text-base outline-none focus:ring-2 focus:ring-blue-500/20 transition-all",
                isImmutable ? disabledBg : inputBg,
                isImmutable && "cursor-not-allowed opacity-80",
                hasError && "border-rose-500 ring-1 ring-rose-500/50"
            )}
        />
    );
};

export default InputWidget;
