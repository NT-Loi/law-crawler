import type { ButtonHTMLAttributes } from 'react';
import { forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className = '', variant = 'primary', size = 'md', children, ...props }, ref) => {
        const baseStyles = 'inline-flex items-center justify-center font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed';

        const variants = {
            primary: 'bg-amber-500 text-slate-900 hover:bg-amber-400 focus:ring-amber-500 shadow-md hover:shadow-lg',
            secondary: 'bg-slate-700 text-slate-100 hover:bg-slate-600 focus:ring-slate-500 border border-slate-600',
            ghost: 'bg-transparent text-slate-300 hover:bg-slate-800 hover:text-slate-100 focus:ring-slate-500',
        };

        const sizes = {
            sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
            md: 'px-4 py-2 text-sm rounded-xl gap-2',
            lg: 'px-6 py-3 text-base rounded-xl gap-2.5',
        };

        return (
            <button
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
                {...props}
            >
                {children}
            </button>
        );
    }
);

Button.displayName = 'Button';

export default Button;
