"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import NProgress from "nprogress";
import "nprogress/nprogress.css";

// Optional logger - can be imported if available
let logger: any = null;
try {
  logger = require("@/lib/logger").logger;
} catch {
  // Fallback logger if the module doesn't exist
  logger = {
    info: (component: string, message: string, data?: any, options?: any) => {
      if (process.env.NODE_ENV === 'development') {
        console.info(`[${component}] ${message}`, data);
      }
    },
    debug: (component: string, message: string, data?: any, options?: any) => {
      if (process.env.NODE_ENV === 'development') {
        console.debug(`[${component}] ${message}`, data);
      }
    }
  };
}

// Configure NProgress
NProgress.configure({
  showSpinner: false,
  minimum: 0.1,
  easing: 'ease',
  speed: 500,
  trickle: true,
  trickleSpeed: 200,
});

export function RouteProgress() {
  const pathname = usePathname();

  // Track when navigation starts and ends
  useEffect(() => {
    logger.info('RouteProgress', `Pathname changed to: ${pathname}`);
    
    // Start progress immediately when pathname changes
    NProgress.start();
    logger.info('RouteProgress', 'Starting NProgress', { pathname });

    // Complete progress after a short delay
    const completeTimer = setTimeout(() => {
      NProgress.done();
      logger.info('RouteProgress', 'NProgress completed');
    }, 300);

    return () => {
      clearTimeout(completeTimer);
    };
  }, [pathname]);

  // Listen for click events on navigation links
  useEffect(() => {
    const handleLinkClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const link = target.closest('a[href]') as HTMLAnchorElement;
      
      if (link && link.href && !link.href.includes('#') && !link.href.includes('javascript:')) {
        // Extract the pathname from the href
        const url = new URL(link.href, window.location.origin);
        const clickedPath = url.pathname;
        
        logger.info('RouteProgress', 'Link clicked', { 
          href: link.href, 
          currentPath: pathname,
          clickedPath 
        }, { sendToServer: true });
        
        // Check if clicking the same page
        if (clickedPath === pathname) {
          logger.info('RouteProgress', 'Same page clicked - showing brief progress', { sendToServer: true });
          
          // Show a brief progress for same-page clicks
          NProgress.start();
          
          // Quick progress animation for same page
          setTimeout(() => {
            NProgress.done();
            logger.info('RouteProgress', 'Same page progress completed');
          }, 200);
          
          return;
        }
        
        // Start progress immediately on click for different page
        NProgress.start();
        logger.info('RouteProgress', 'NProgress started immediately on click', { sendToServer: true });
      }
    };

    // Add click listener to all navigation links
    document.addEventListener('click', handleLinkClick);

    return () => {
      document.removeEventListener('click', handleLinkClick);
    };
  }, [pathname]);

  // Monitor page load completion
  useEffect(() => {
    const checkPageLoaded = () => {
      // Check if the page content is fully loaded
      const mainContent = document.querySelector('main');
      if (mainContent && mainContent.children.length > 0) {
        logger.info('RouteProgress', 'Page content detected as loaded', { sendToServer: true });
        NProgress.done();
        logger.info('RouteProgress', 'NProgress hidden after page load detection');
      }
    };

    // Check after a short delay to allow content to load
    const loadCheckTimer = setTimeout(checkPageLoaded, 100);

    return () => {
      clearTimeout(loadCheckTimer);
    };
  }, [pathname]);

  // Don't render anything - NProgress handles the UI
  return null;
} 