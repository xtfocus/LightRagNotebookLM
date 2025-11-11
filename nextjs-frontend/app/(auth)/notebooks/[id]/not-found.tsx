import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeft, FileText } from 'lucide-react';

export default function NotebookNotFound() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center max-w-md mx-auto p-6">
        <div className="mb-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="h-8 w-8 text-red-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Notebook Not Found
          </h1>
          <p className="text-gray-600 mb-6">
            The notebook you're looking for doesn't exist or you don't have permission to access it.
          </p>
        </div>
        
        <div className="space-y-3">
          <Link href="/notebooks">
            <Button className="w-full">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Notebooks
            </Button>
          </Link>
          
          <Link href="/notebooks">
            <Button variant="outline" className="w-full">
              Create New Notebook
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
} 