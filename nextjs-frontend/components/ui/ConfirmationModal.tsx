'use client';

import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { BaseModal } from '@/components/ui/BaseModal';
import { colors } from '@/lib/design-system';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  isLoading?: boolean;
}

export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'danger',
  isLoading = false,
}: ConfirmationModalProps) {
  const handleConfirm = () => {
    if (!isLoading) {
      onConfirm();
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'danger':
        return {
          iconColor: colors.red[500],
          confirmButtonVariant: 'destructive' as const,
        };
      case 'warning':
        return {
          iconColor: colors.yellow[500],
          confirmButtonVariant: 'default' as const,
        };
      case 'info':
        return {
          iconColor: colors.primary[500],
          confirmButtonVariant: 'default' as const,
        };
      default:
        return {
          iconColor: colors.red[500],
          confirmButtonVariant: 'destructive' as const,
        };
    }
  };

  const { iconColor, confirmButtonVariant } = getVariantStyles();

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={handleClose}
      title={title}
      disabled={isLoading}
      maxWidth="max-w-sm"
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <AlertTriangle 
            className="h-5 w-5 mt-0.5 flex-shrink-0" 
            style={{ color: iconColor }}
          />
          <p className="text-sm text-gray-600 leading-relaxed">
            {message}
          </p>
        </div>
        
        <div className="flex justify-end gap-3 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isLoading}
          >
            {cancelText}
          </Button>
          <Button
            type="button"
            variant={confirmButtonVariant}
            onClick={handleConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : confirmText}
          </Button>
        </div>
      </div>
    </BaseModal>
  );
} 