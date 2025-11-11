"use client";

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { createNotebook } from '@/components/actions/notebooks-action';
import { showErrorNotification, isNextRedirectError } from '@/lib/error-handling';
import { useNotifications } from '@/components/ui/NotificationContext';
import { BaseModal, BaseModalForm } from '@/components/ui/BaseModal';

interface CreateNotebookModalProps {
  isOpen?: boolean;
  onClose?: () => void;
  externalIsOpen?: boolean;
  externalOnClose?: () => void;
}

export function CreateNotebookModal({ 
  isOpen: externalIsOpen, 
  onClose: externalOnClose 
}: CreateNotebookModalProps = {}) {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { addNotification } = useNotifications();

  // Determine if modal is controlled externally or internally
  const isControlled = externalIsOpen !== undefined;
  const isOpen = isControlled ? externalIsOpen : internalIsOpen;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const result = await createNotebook({ title: title.trim(), description: description.trim() });
      if (result && typeof result === 'object' && 'message' in result) {
        showErrorNotification(addNotification, result, 'Notebook Creation');
        return;
      }
    } catch (error: any) {
              if (isNextRedirectError(error)) {
          setTitle('');
          setDescription('');
          if (isControlled) {
            if (externalOnClose) { externalOnClose(); }
          } else {
            setInternalIsOpen(false);
          }
          return;
        }
      showErrorNotification(addNotification, error, 'Notebook Creation');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setTitle('');
    setDescription('');
    if (isControlled) {
      if (externalOnClose) { externalOnClose(); }
    } else {
      setInternalIsOpen(false);
    }
  };

  return (
    <>
      {!isControlled && (
        <Button
          onClick={() => setInternalIsOpen(true)}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          New Notebook
        </Button>
      )}

      <BaseModal
        isOpen={isOpen}
        onClose={handleClose}
        title="Create New Notebook"
        disabled={isSubmitting}
      >
        <BaseModalForm
          onSubmit={handleSubmit}
          submitText="Create Notebook"
          onCancel={handleClose}
          isSubmitting={isSubmitting}
          submitDisabled={!title.trim()}
        >
          <div>
            <Label htmlFor="title" className="text-sm font-medium text-gray-700">
              Title *
            </Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter notebook title"
              required
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="description" className="text-sm font-medium text-gray-700">
              Description
            </Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter notebook description (optional)"
              rows={3}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </BaseModalForm>
      </BaseModal>
    </>
  );
} 