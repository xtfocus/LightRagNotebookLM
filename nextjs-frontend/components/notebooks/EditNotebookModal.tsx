"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NotebookPublic } from "@/app/openapi-client/types.gen";
import { useNotebooks } from "@/contexts/NotebookContext";
import { BaseModal, BaseModalForm } from "@/components/ui/BaseModal";

interface EditNotebookModalProps {
  notebook: NotebookPublic | null;
  isOpen: boolean;
}

export function EditNotebookModal({ notebook, isOpen }: EditNotebookModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { closeEditModal, handleSaveEdit } = useNotebooks();

  useEffect(() => {
    if (notebook) {
      setTitle(notebook.title);
      setDescription(notebook.description || "");
    }
  }, [notebook]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notebook || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await handleSaveEdit(notebook.id, title.trim(), description.trim());
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      closeEditModal();
    }
  };

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={handleClose}
      title="Edit Notebook"
      disabled={isSubmitting}
    >
      <BaseModalForm
        onSubmit={handleSubmit}
        submitText="Save Changes"
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
            disabled={isSubmitting}
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
            disabled={isSubmitting}
            rows={3}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </BaseModalForm>
    </BaseModal>
  );
} 