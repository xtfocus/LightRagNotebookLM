'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Menu, X, Info, BookOpen, FileText } from 'lucide-react';

interface BurgerMenuProps {
  className?: string;
}

export function BurgerMenu({ className = '' }: BurgerMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  const menuItems = [
    {
      href: '/about',
      label: 'About',
      icon: Info,
      description: 'Learn more about OpenStorm'
    },
    {
      href: '/using-openstorm',
      label: 'Using OpenStorm',
      icon: BookOpen,
      description: 'How to use our platform'
    },
    {
      href: '/blog',
      label: 'Blog',
      icon: FileText,
      description: 'Latest updates and insights'
    }
  ];

  return (
    <div className={`relative ${className}`}>
      {/* Burger Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleMenu}
        className="h-12 w-12 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
        aria-label="Toggle menu"
      >
        <Menu className="h-6 w-6" />
      </Button>

      {/* Sidebar Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 bg-black/20" onClick={closeMenu}>
          {/* Sliding Sidebar */}
          <div 
            className={`absolute top-0 right-0 h-full w-80 bg-white dark:bg-gray-800 shadow-lg border-l border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out ${
              isOpen ? 'translate-x-0' : 'translate-x-full'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Sidebar Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Menu
              </h2>
              <Button
                variant="ghost"
                size="icon"
                onClick={closeMenu}
                className="h-10 w-10"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Sidebar Content */}
            <div className="p-6">
              {/* Navigation Items */}
              <div className="space-y-3">
                {menuItems.map((item) => {
                  const IconComponent = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={closeMenu}
                      className="flex items-center gap-4 p-4 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <IconComponent className="h-6 w-6 text-gray-500 dark:text-gray-400" />
                      <div className="flex-1 text-left">
                        <div className="font-medium text-gray-900 dark:text-white text-base">
                          {item.label}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {item.description}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 