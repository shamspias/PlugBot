import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
}

export class Card extends React.Component<CardProps> {
    render() {
        const {children, className = ''} = this.props;
        return (
            <div className={`bg-white rounded-lg shadow-md ${className}`}>
                {children}
            </div>
        );
    }
}

export class CardHeader extends React.Component<CardProps> {
    render() {
        const {children, className = ''} = this.props;
        return (
            <div className={`px-6 py-4 border-b border-gray-200 ${className}`}>
                {children}
            </div>
        );
    }
}

export class CardContent extends React.Component<CardProps> {
    render() {
        const {children, className = ''} = this.props;
        return (
            <div className={`px-6 py-4 ${className}`}>
                {children}
            </div>
        );
    }
}