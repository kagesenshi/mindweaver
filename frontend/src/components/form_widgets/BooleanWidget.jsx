/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React from 'react';
import { cn } from '../../utils/cn';

/**
 * BooleanWidget - Toggle switch for boolean fields
 */
const BooleanWidget = ({ 
    name, 
    formData, 
    onChange, 
    darkMode, 
    isImmutable, 
    hasError,
    inputBg 
}) => {
    return (
        <div className={cn(
            "flex items-center gap-3 px-4 h-[50px] rounded-xl border cursor-pointer select-none transition-all",
            isImmutable ? (darkMode ? "bg-slate-900 border-slate-800" : "bg-slate-200 border-slate-300") : (formData[name] ? "border-blue-500/50 bg-blue-500/5" : inputBg),
            hasError && "border-rose-500 ring-1 ring-rose-500/50",
            isImmutable && "cursor-not-allowed opacity-80"
        )} onClick={() => !isImmutable && onChange(name, !formData[name])}>
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
};

export default BooleanWidget;
