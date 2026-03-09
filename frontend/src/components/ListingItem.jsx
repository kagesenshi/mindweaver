/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

import React from 'react';

/**
 * A standardized component for list items used across the application.
 * 
 * @param {Object} props
 * @param {React.ElementType} props.icon - Icon component to display
 * @param {string} props.title - Primary text
 * @param {string|React.ReactNode} props.subtitle - Secondary text
 * @param {Array<{text: string, variant: string}>} [props.badges] - Optional badges to display next to title
 * @param {React.ReactNode} [props.actions] - Optional action buttons/elements on the right
 * @param {Function} [props.onClick] - Click handler for the whole item
 * @param {string} [props.className] - Additional classes for the container
 */
const ListingItem = ({
    icon: Icon,
    title,
    subtitle,
    badges = [],
    actions,
    onClick,
    className = ""
}) => {
    return (
        <div
            className={`mw-list-item group ${className}`}
            onClick={onClick}
        >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 w-full">
                <div className="flex items-center gap-6">
                    <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0">
                        {Icon && <Icon className="w-6 h-6 text-slate-600 dark:text-slate-400" />}
                    </div>

                    <div>
                        <div className="flex items-center gap-3 flex-wrap">
                            <h4 className="text-lg font-bold text-slate-900 dark:text-white">
                                {title}
                            </h4>
                            {badges.map((badge, idx) => (
                                <span key={idx} className={badge.variant || "mw-badge-neutral"}>
                                    {badge.text}
                                </span>
                            ))}
                        </div>
                        <div className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                            {subtitle}
                        </div>
                    </div>
                </div>

                {actions && (
                    <div className="flex items-center gap-2">
                        {actions}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ListingItem;
