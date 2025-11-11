'use client';

import { useEffect } from 'react';

export default function NotebookWorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    // Prevent body scrolling when notebook workspace is active
    document.body.style.overflow = 'hidden';
    
    return () => {
      // Restore body scrolling when leaving notebook workspace
      document.body.style.overflow = 'auto';
    };
  }, []);

  return (
    <div className="h-screen overflow-hidden" style={{ maxHeight: '100vh' }}>
      {children}
    </div>
  );
} 