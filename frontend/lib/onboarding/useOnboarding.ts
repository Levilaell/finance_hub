'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  DESKTOP_TOUR_STEPS,
  MOBILE_TOUR_STEPS,
  TOUR_CONFIG,
  STORAGE_KEYS,
  LG_BREAKPOINT,
} from './config';
import 'driver.js/dist/driver.css';
import './styles.css';

export function useOnboarding() {
  const router = useRouter();
  const pathname = usePathname();
  const driverRef = useRef<any>(null);

  const isMobile = () => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < LG_BREAKPOINT;
  };

  const shouldShowTour = useCallback(() => {
    if (typeof window === 'undefined') return false;

    const showTour = localStorage.getItem(STORAGE_KEYS.SHOW_TOUR);
    const tourDone = localStorage.getItem(STORAGE_KEYS.TOUR_DONE);

    return showTour === 'true' && tourDone !== 'true';
  }, []);

  const openMobileSidebar = () => {
    window.dispatchEvent(new CustomEvent('tour:open-sidebar'));
  };

  const closeMobileSidebar = () => {
    window.dispatchEvent(new CustomEvent('tour:close-sidebar'));
  };

  const startTour = useCallback(async () => {
    if (typeof window === 'undefined') return;

    const { driver } = await import('driver.js');
    const mobile = isMobile();
    const steps = mobile ? MOBILE_TOUR_STEPS : DESKTOP_TOUR_STEPS;

    const driverInstance = driver({
      ...TOUR_CONFIG,
      steps: steps.map((step, index) => ({
        ...step,
        popover: {
          ...step.popover,
          // First step: "Vamos!" button
          ...(index === 0 && {
            nextBtnText: 'Vamos!',
          }),
          // Last step: "Conectar Banco" button
          ...(index === steps.length - 1 && {
            nextBtnText: 'Conectar Banco',
          }),
        },
      })),
      onHighlightStarted: (element) => {
        const el = element as HTMLElement | undefined;
        const tourAttr = el?.getAttribute?.('data-tour');

        // Mobile: Open sidebar before highlighting menu items
        if (mobile && tourAttr === 'contas-mobile') {
          openMobileSidebar();
          // Small delay to let sidebar animation complete
          return new Promise((resolve) => setTimeout(resolve, 300));
        }
      },
      onNextClick: (element) => {
        const currentIndex = driverInstance.getActiveIndex();
        const el = element as HTMLElement | undefined;
        const tourAttr = el?.getAttribute?.('data-tour');

        if (mobile) {
          // Mobile flow
          // After showing "Contas Bancárias" in sidebar, navigate to /accounts
          if (tourAttr === 'contas-mobile') {
            closeMobileSidebar();
            if (pathname !== '/accounts') {
              router.push('/accounts');
              // Wait for navigation and page load, then continue
              setTimeout(() => {
                driverInstance.moveNext();
              }, 500);
              return;
            }
          }
        } else {
          // Desktop flow
          // After highlighting sidebar item, navigate to /accounts
          if (tourAttr === 'contas-desktop') {
            if (pathname !== '/accounts') {
              router.push('/accounts');
              // Wait for navigation and page load, then continue
              setTimeout(() => {
                driverInstance.moveNext();
              }, 500);
              return;
            }
          }
        }

        driverInstance.moveNext();
      },
      onPrevClick: () => {
        const currentIndex = driverInstance.getActiveIndex();

        if (mobile) {
          // If going back from "conectar-banco" step, we might need to open sidebar again
          // to show contas-mobile
          if (currentIndex !== undefined) {
            const prevStep = steps[currentIndex - 1];
            const prevTourAttr = prevStep?.element?.toString().match(/data-tour="([^"]+)"/)?.[1];

            if (prevTourAttr === 'contas-mobile') {
              openMobileSidebar();
            }
          }
        }

        driverInstance.movePrevious();
      },
      onDestroyStarted: () => {
        // Close sidebar if open
        if (mobile) {
          closeMobileSidebar();
        }

        // Only mark as done if user completed the tour (clicked last button)
        if (driverInstance.isLastStep()) {
          localStorage.setItem(STORAGE_KEYS.TOUR_DONE, 'true');
          localStorage.removeItem(STORAGE_KEYS.SHOW_TOUR);
          driverInstance.destroy();
          // Navigate to accounts if not already there
          if (pathname !== '/accounts') {
            router.push('/accounts');
          }
        } else {
          // User closed early - just destroy, don't mark as done
          driverInstance.destroy();
        }
      },
    });

    driverRef.current = driverInstance;
    driverInstance.drive();
  }, [router, pathname]);

  const resetTour = useCallback(() => {
    if (typeof window === 'undefined') return;

    localStorage.removeItem(STORAGE_KEYS.TOUR_DONE);
    localStorage.setItem(STORAGE_KEYS.SHOW_TOUR, 'true');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (driverRef.current) {
        driverRef.current.destroy();
      }
    };
  }, []);

  return {
    shouldShowTour,
    startTour,
    resetTour,
  };
}
