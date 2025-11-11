"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { CreateNotebookModal } from "@/components/notebooks/CreateNotebookModal";

interface CreateNotebookTileProps {
  onNotebookCreated?: () => void;
}

export function CreateNotebookTile({ onNotebookCreated }: CreateNotebookTileProps = {}) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleClose = () => {
    setIsModalOpen(false);
    // Call the callback to refresh the parent's notebook list
    if (onNotebookCreated) {
      onNotebookCreated();
    }
  };

  return (
    <>
      <Card 
        className="hover:shadow-lg transition-shadow cursor-pointer border-2 border-dashed border-gray-300 hover:border-gray-400 group h-full"
        onClick={() => setIsModalOpen(true)}
        style={{ minHeight: '200px' }}
      >
        <CardContent className="flex flex-col items-center justify-center h-full p-8">
          <div className="flex flex-col items-center gap-6">
            <div className="w-20 h-20 rounded-full bg-blue-50 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
              <Plus className="h-12 w-12 text-blue-600" />
            </div>
            <span className="text-xl font-semibold text-gray-700 text-center">
              Create new notebook
            </span>
          </div>
        </CardContent>
      </Card>
      
      <CreateNotebookModal 
        isOpen={isModalOpen} 
        onClose={handleClose} 
      />
    </>
  );
} 