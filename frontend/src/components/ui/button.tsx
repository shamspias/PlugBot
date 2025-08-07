import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning';
    size?: 'sm' | 'md' | 'lg';
}

export class Button extends React.Component<ButtonProps> {
    render() {
        const {
            variant = 'primary',
            size = 'md',
            className = '',
            children,
            disabled,
            ...props
        } = this.props;

        const baseClasses = 'font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';

        const variantClasses = {
            primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
            secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
            danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
            success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
            warning: 'bg-yellow-500 text-white hover:bg-yellow-600 focus:ring-yellow-500',
        };

        const sizeClasses = {
            sm: 'px-3 py-1.5 text-sm',
            md: 'px-4 py-2 text-base',
            lg: 'px-6 py-3 text-lg',
        };

        const disabledClasses = disabled ? 'opacity-50 cursor-not-allowed' : '';

        return (
            <button
                className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${disabledClasses} ${className}`}
                disabled={disabled}
                {...props}
            >
                {children}
            </button>
        );
    }
}
