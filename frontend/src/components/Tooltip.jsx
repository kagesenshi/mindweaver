import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../utils/cn';

export const Tooltip = ({ children, content, side = 'right', className, disabled = false }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [position, setPosition] = useState({ top: 0, left: 0 });
    const triggerRef = useRef(null);

    const updatePosition = useCallback(() => {
        if (triggerRef.current) {
            const rect = triggerRef.current.getBoundingClientRect();
            // Simple right-side positioning for sidebar use case
            if (side === 'right') {
                setPosition({
                    top: rect.top + (rect.height / 2),
                    left: rect.right + 8
                });
            }
        }
    }, [side]);

    useEffect(() => {
        if (isVisible) {
            updatePosition();
            window.addEventListener('scroll', updatePosition);
            window.addEventListener('resize', updatePosition);
        }
        return () => {
            window.removeEventListener('scroll', updatePosition);
            window.removeEventListener('resize', updatePosition);
        };
    }, [isVisible, updatePosition]);

    if (disabled) return children;

    return (
        <div
            ref={triggerRef}
            onMouseEnter={() => {
                updatePosition();
                setIsVisible(true);
            }}
            onMouseLeave={() => setIsVisible(false)}
            className="w-full"
        >
            {children}
            {isVisible && createPortal(
                <div
                    className={cn(
                        "fixed z-[9999] px-2 py-1 text-sm font-medium text-white bg-slate-900 rounded shadow-lg pointer-events-none transform -translate-y-1/2 whitespace-nowrap animate-in fade-in zoom-in-95 duration-200",
                        className
                    )}
                    style={{
                        top: position.top,
                        left: position.left,
                    }}
                >
                    {content}
                    {/* Tiny arrow pointing left */}
                    <div className="absolute top-1/2 -left-1 w-2 h-2 bg-slate-900 rotate-45 -translate-y-1/2" />
                </div>,
                document.body
            )}
        </div>
    );
};
