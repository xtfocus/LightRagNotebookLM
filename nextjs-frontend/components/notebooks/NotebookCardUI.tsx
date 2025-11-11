import Link from "next/link";
import { BookOpen, MoreVertical, Edit, Trash2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { notebook as notebookDesign, transitions } from '@/lib/design-system';
import { NotebookCardUIProps } from '@/types/notebook';
import { useState, useRef, useEffect } from 'react';

export function NotebookCardUI({
  id,
  title,
  description,
  updatedAt,
  sourceCount,
  onEdit,
  onDelete,
  onDeleteClick,
  isDeleting,
  formattedDate,
}: NotebookCardUIProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const titleRef = useRef<HTMLDivElement>(null);

  const handleDropdownClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const updateTooltipPosition = () => {
    if (titleRef.current) {
      const rect = titleRef.current.getBoundingClientRect();
      setTooltipPosition({
        top: rect.top - 10,
        left: rect.left
      });
    }
  };

  useEffect(() => {
    if (showTooltip) {
      updateTooltipPosition();
    }
  }, [showTooltip]);

  return (
    <Link href={`/notebooks/${id}`} className="block">
      <Card className="hover:shadow-lg transition-shadow group h-full cursor-pointer flex flex-col" style={{ minHeight: '200px' }}>
        <CardHeader className="pb-3 flex-shrink-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-4 flex-1 min-w-0">
              <BookOpen 
                className="h-10 w-10 mt-1 flex-shrink-0" 
                style={{ color: notebookDesign.colors.icon }}
              />
              <div className="flex-1 min-w-0">
                <div 
                  ref={titleRef}
                  className="relative inline-block w-full"
                  onMouseEnter={() => setShowTooltip(true)}
                  onMouseLeave={() => setShowTooltip(false)}
                >
                  <CardTitle className="text-2xl font-semibold text-gray-900 line-clamp-2 break-words">
                    {title}
                  </CardTitle>
                </div>
                {description && (
                  <CardDescription className="mt-2 text-gray-600 line-clamp-2 text-base break-words">
                    {description}
                  </CardDescription>
                )}
              </div>
            </div>
            <div className="flex-shrink-0 relative">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button 
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-gray-100 rounded"
                    style={{ transition: transitions.fast }}
                    onClick={handleDropdownClick}
                  >
                    <MoreVertical className="h-5 w-5 text-gray-500" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent 
                  align="end" 
                  side="bottom"
                  sideOffset={4}
                  className="min-w-[160px]"
                  onClick={handleDropdownClick}
                >
                  <DropdownMenuItem onClick={(e) => { e.preventDefault(); e.stopPropagation(); onEdit(); }}>
                    <Edit className="h-5 w-5 mr-3" />
                    Edit title
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDeleteClick(); }}
                    disabled={isDeleting}
                    className="text-red-600 focus:text-red-600"
                  >
                    <Trash2 className="h-5 w-5 mr-3" />
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0 flex-1 flex flex-col justify-end">
          <div className="flex items-center justify-between text-base text-gray-500">
            <span>Updated {formattedDate}</span>
            <span 
              className="px-3 py-1 rounded-full text-sm"
              style={{ 
                backgroundColor: notebookDesign.colors.badge,
                color: notebookDesign.colors.badgeText
              }}
            >
              {sourceCount} sources
            </span>
          </div>
        </CardContent>
      </Card>
      
      {/* Tooltip rendered outside card to avoid overflow issues */}
      {showTooltip && (
        <div 
          className="fixed px-3 py-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg z-[9999] max-w-xs break-words whitespace-normal pointer-events-none"
          style={{
            top: `${tooltipPosition.top}px`,
            left: `${tooltipPosition.left}px`,
            transform: 'translateY(-100%)'
          }}
        >
          {title}
        </div>
      )}
    </Link>
  );
} 