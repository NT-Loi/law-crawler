import type { HTMLAttributes } from 'react';
import { forwardRef } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
    variant?: 'default' | 'elevated' | 'glass';
    padding?: 'none' | 'sm' | 'md' | 'lg';
}

const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className = '', variant = 'default', padding = 'md', children, ...props }, ref) => {
        const variants = {
            default: 'bg-slate-800/50 border border-slate-700/50',
            elevated: 'bg-slate-800 border border-slate-700 shadow-lg',
            glass: 'glass',
        };

        const paddings = {
            none: '',
            sm: 'p-3',
            md: 'p-4',
            lg: 'p-6',
        };

        return (
            <div
                ref={ref}
                className={`rounded-2xl ${variants[variant]} ${paddings[padding]} ${className}`}
                {...props}
            >
                {children}
            </div>
        );
    }
);

Card.displayName = 'Card';

export default Card;
