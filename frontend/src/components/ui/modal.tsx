import React from 'react';
import {X} from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
}

export class Modal extends React.Component<ModalProps> {
    componentDidMount() {
        document.addEventListener('keydown', this.handleEscape);
    }

    componentWillUnmount() {
        document.removeEventListener('keydown', this.handleEscape);
    }

    handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && this.props.isOpen) {
            this.props.onClose();
        }
    };

    render() {
        const {isOpen, onClose, title, children} = this.props;

        if (!isOpen) return null;

        return (
            <div className="fixed inset-0 z-50 overflow-y-auto">
                <div className="flex min-h-screen items-center justify-center p-4">
                    <div
                        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
                        onClick={onClose}
                    />
                    <div
                        className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="flex items-center justify-between p-4 border-b">
                            <h2 className="text-xl font-semibold">{title}</h2>
                            <button
                                onClick={onClose}
                                className="text-gray-400 hover:text-gray-600 transition-colors"
                            >
                                <X size={24}/>
                            </button>
                        </div>
                        <div className="p-6">{children}</div>
                    </div>
                </div>
            </div>
        );
    }
}
