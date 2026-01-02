import type { InputHTMLAttributes } from 'react';
import { forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    icon?: React.ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ className = '', icon, ...props }, ref) => {
        return (
            <div className="relative flex items-center">
                {icon && (
                    <div className="absolute left-4 text-slate-400 pointer-events-none">
                        {icon}
                    </div>
                )}
                <input
                    ref={ref}
                    className={`
            w-full bg-slate-800/50 border border-slate-700 rounded-xl
            px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500
            focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500
            transition-all duration-200
            ${icon ? 'pl-12' : ''}
            ${className}
          `}
                    {...props}
                />
            </div>
        );
    }
);

Input.displayName = 'Input';

export default Input;
