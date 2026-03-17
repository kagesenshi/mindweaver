/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React from 'react';
import { cn } from '../../utils/cn';

/**
 * RangeWidget - Custom range input with badge and steps
 */
const RangeWidget = ({ 
    name, 
    widget, 
    formData, 
    onChange, 
    darkMode, 
    isImmutable 
}) => {
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
                    onChange={(e) => onChange(name, parseFloat(e.target.value))}
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
};

export default RangeWidget;
