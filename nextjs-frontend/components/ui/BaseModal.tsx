'use client';

import React, { ReactNode } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { components, zIndex } from '@/lib/design-system';

interface BaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  maxWidth?: string;
  showCloseButton?: boolean;
  disabled?: boolean;
  className?: string;
}

export function BaseModal({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = components.modal.maxWidth.md,
  showCloseButton = true,
  disabled = false,
  className = '',
}: BaseModalProps) {
  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !disabled) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      style={{ zIndex: zIndex.modal }}
      onClick={handleBackdropClick}
    >
      <div className={`bg-white rounded-lg p-6 w-full mx-4 ${maxWidth} ${className}`}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          {showCloseButton && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              disabled={disabled}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        {children}
      </div>
    </div>
  );
}

interface BaseModalFormProps {
  children: ReactNode;
  onSubmit: (e: React.FormEvent) => void;
  submitText: string;
  cancelText?: string;
  onCancel?: () => void;
  isSubmitting?: boolean;
  submitDisabled?: boolean;
  className?: string;
}

export function BaseModalForm({
  children,
  onSubmit,
  submitText,
  cancelText = 'Cancel',
  onCancel,
  isSubmitting = false,
  submitDisabled = false,
  className = '',
}: BaseModalFormProps) {
  const handleCancel = () => {
    if (!isSubmitting && onCancel) {
      onCancel();
    }
  };

  return (
    <form onSubmit={onSubmit} className={`space-y-4 ${className}`}>
      {children}
      <div className="flex justify-end gap-3 pt-4">
        {onCancel && (
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            {cancelText}
          </Button>
        )}
        <Button
          type="submit"
          disabled={isSubmitting || submitDisabled}
        >
          {isSubmitting ? 'Loading...' : submitText}
        </Button>
      </div>
    </form>
  );
} 