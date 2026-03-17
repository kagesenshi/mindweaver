/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React from 'react';
import { cn } from '../../utils/cn';

/**
 * PasswordWidget - Scrambled input for sensitive information
 */
const PasswordWidget = ({ 
    name, 
    label, 
    widget, 
    formData, 
    onChange, 
    isImmutable, 
    disabledBg, 
    inputBg, 
    hasError 
}) => {
    return (
        <input
            type="password"
            value={formData[name] ?? ''}
            disabled={isImmutable}
            onChange={(e) => onChange(name, e.target.value)}
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

export default PasswordWidget;
