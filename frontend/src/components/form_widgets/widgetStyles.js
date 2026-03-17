/*
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
*/

/**
 * Shared styles for react-select used in DynamicForm widgets
 */
export const getSelectStyles = (darkMode, hasError) => ({
    control: (base, state) => ({
        ...base,
        background: state.isDisabled
            ? (darkMode ? '#0f172a' : '#e2e8f0') // slate-900 : slate-200
            : (darkMode ? '#020617' : '#f1f5f9'), // slate-950 : slate-100
        borderColor: state.isDisabled
            ? (darkMode ? '#1e293b' : '#cbd5e1') // slate-800 : slate-300
            : (hasError ? '#f43f5e' : (darkMode ? '#1e293b' : '#e2e8f0')), // rose-500 : slate-800 : slate-200
        color: state.isDisabled
            ? (darkMode ? '#64748b' : '#94a3b8') // slate-500 : slate-400
            : (darkMode ? '#e2e8f0' : '#0f172a'),
        minHeight: '50px',
        borderRadius: '0.75rem',
        boxShadow: state.isFocused ? '0 0 0 1px rgba(59, 130, 246, 0.5)' : 'none',
        opacity: state.isDisabled ? 0.8 : 1,
        cursor: state.isDisabled ? 'not-allowed' : 'default',
        '&:hover': {
            borderColor: state.isDisabled
                ? (darkMode ? '#1e293b' : '#cbd5e1')
                : (darkMode ? '#334155' : '#cbd5e1')
        }
    }),
    menu: (base) => ({
        ...base,
        background: darkMode ? '#020617' : '#ffffff',
        border: `1px solid ${darkMode ? '#1e293b' : '#e2e8f0'}`,
        zIndex: 100
    }),
    option: (base, state) => ({
        ...base,
        backgroundColor: state.isFocused
            ? (darkMode ? '#1e293b' : '#e2e8f0')
            : (state.isSelected ? (darkMode ? '#3b82f6' : '#bfdbfe') : 'transparent'),
        color: state.isSelected && darkMode ? '#ffffff' : (darkMode ? '#e2e8f0' : '#0f172a'),
        cursor: 'pointer'
    }),
    singleValue: (base, state) => ({
        ...base,
        color: state.isDisabled
            ? (darkMode ? '#64748b' : '#94a3b8')
            : (darkMode ? '#e2e8f0' : '#0f172a'),
    }),
    multiValue: (base) => ({
        ...base,
        backgroundColor: darkMode ? '#1e293b' : '#e2e8f0',
    }),
    multiValueLabel: (base) => ({
        ...base,
        color: darkMode ? '#e2e8f0' : '#0f172a',
    }),
    input: (base) => ({
        ...base,
        color: darkMode ? '#e2e8f0' : '#0f172a',
    })
});
