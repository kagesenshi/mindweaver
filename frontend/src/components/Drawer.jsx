import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '../utils/cn';

const Drawer = ({
    trigger,
    children,
    isOpen: controlledIsOpen,
    onOpenChange,
    placement = 'bottom',
    className,
    darkMode = false,
    activeBg,
}) => {
    const [internalIsOpen, setInternalIsOpen] = useState(false);
    const isControlled = controlledIsOpen !== undefined;
    const isOpen = isControlled ? controlledIsOpen : internalIsOpen;

    const containerRef = useRef(null);

    const handleOpenChange = useCallback((newState) => {
        if (!isControlled) {
            setInternalIsOpen(newState);
        }
        if (onOpenChange) {
            onOpenChange(newState);
        }
    }, [isControlled, onOpenChange]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                handleOpenChange(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen, handleOpenChange]);

    // Active drawer background - needed for the "patch" to hide the seam
    // Default to strict black for dark mode if not specified, compatible with Header
    const finalActiveBg = activeBg || (darkMode ? "bg-[#08090b]" : "bg-white");

    // Styles based on placement
    // Top placement (opens UP): Button rounded-t-xl, Dropdown rounded-t-xl rounded-b-none... NO wait.
    // UserProfilePanel (placement top): Panel is at bottom, opens UP. 
    //   Button: default rounded-xl.
    //   Open: rounded-t-none rounded-b-xl. Dropdown: top-[...]? No, UserProfilePanel is at bottom of sidebar?
    //   Let's check UserProfilePanel again.
    //   UserProfilePanel: "absolute bottom-[calc(100%-1px)]" -> Drawer appears ABOVE the trigger.
    //   Trigger: "rounded-t-none ... rounded-b-xl" when open.

    // Header (placement bottom):
    //   Dropdown: "top-[calc(100%-1px)]" -> Drawer appears BELOW the trigger.
    //   Trigger: "rounded-b-none ... rounded-t-xl" when open.

    const isTop = placement === 'top';

    return (
        <div className={cn("relative", className)} ref={containerRef}>
            <div
                className={cn(
                    "transition-all duration-300 relative outline-none",
                    isOpen
                        ? cn(
                            "z-50 ring-2 ring-blue-500/20",
                            isTop
                                ? "rounded-t-none rounded-b-xl" // Trigger opens UP, so it connects at top.
                                : "rounded-b-none rounded-t-xl", // Trigger opens DOWN, so it connects at bottom.
                            finalActiveBg
                        )
                        : "rounded-xl hover:ring-2 hover:ring-blue-500/20"
                )}
            >
                {/* 
                   The trigger rendering validation. 
                   If trigger is a function, call it with { isOpen }.
                   Else render it directly, wrapping in a click handler if it's not interactive?
                   Usually giving `onClick` to the container div or cloneElement.
                   For maximum flexibility let's wrap in a div or require trigger to be interactive.
                   Actually, let's just make this div the interactive element if we want, OR
                   clone element.
                   
                   Better approach: Just render the trigger content inside this styled container wrapper.
                   But wait, Header has `button` as the trigger.
                   Reference implementation had the `button` CARRY the styles.
                   So we should probably render a div that LOOKS like the button, or
                   let the user pass the button?
                   
                   Refactoring:
                   Header: `<button ... className="..." > ... </button>`
                   The styles are on the button.
                   
                   If Drawer wraps the button, Drawer needs to handle the click.
                */}
                <div
                    onClick={() => handleOpenChange(!isOpen)}
                    className="cursor-pointer"
                >
                    {isOpen && (
                        <div className={cn(
                            "absolute left-0 right-0 h-2 z-50",
                            finalActiveBg,
                            isTop ? "-top-1" : "-bottom-1"
                        )} />
                    )}
                    {typeof trigger === 'function' ? trigger({ isOpen }) : trigger}
                </div>
            </div>

            {isOpen && (
                <div className={cn(
                    "absolute left-0 right-0 z-40 p-1.5 shadow-xl ring-2 ring-blue-500/20",
                    "transition-all animate-in fade-in zoom-in-95 duration-200",
                    finalActiveBg,
                    isTop
                        ? "bottom-[calc(100%-1px)] rounded-t-xl rounded-b-none slide-in-from-bottom-2"
                        : "top-[calc(100%-1px)] rounded-b-xl rounded-t-none slide-in-from-top-2",
                )}>
                    {children}
                </div>
            )}
        </div>
    );
};

export default Drawer;
