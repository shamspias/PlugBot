import React from 'react';

interface BadgeProps {
    variant?: 'success' | 'danger' | 'warning' | 'info' | 'default';
    children: React.ReactNode;
    className?: string;
}

export class Badge extends React.Component<BadgeProps> {
    render() {
        const {variant = 'default', children, className = ''} = this.props;

        const variantClasses = {
            success: 'bg-green-100 text-green-800',
            danger: 'bg-red-100 text-red-800',
            warning: 'bg-yellow-100 text-yellow-800',
            info: 'bg-blue-100 text-blue-800',
            default: 'bg-gray-100 text-gray-800',
        };

        return (
            <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]} ${className}`}
            >
        {children}
      </span>
        );
    }
}