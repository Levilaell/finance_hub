'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { TOUR_STEPS, TOUR_CONFIG, STORAGE_KEYS } from './config';
import 'driver.js/dist/driver.css';
import './styles.css';

export function useOnboarding() {
  const router = useRouter();
  const driverRef = useRef<any>(null);

  const shouldShowTour = useCallback(() => {
    if (typeof window === 'undefined') return false;

    const showTour = localStorage.getItem(STORAGE_KEYS.SHOW_TOUR);
    const tourDone = localStorage.getItem(STORAGE_KEYS.TOUR_DONE);

    return showTour === 'true' && tourDone !== 'true';
  }, []);

  const startTour = useCallback(async () => {
    if (typeof window === 'undefined') return;

    // Dynamic import to avoid SSR issues
    const { driver } = await import('driver.js');

    const driverInstance = driver({
      ...TOUR_CONFIG,
      steps: TOUR_STEPS.map((step, index) => ({
        ...step,
        popover: {
          ...step.popover,
          // Custom button text for last step
          ...(index === TOUR_STEPS.length - 1 && {
            nextBtnText: 'Conectar Banco',
          }),
          // First step has different button
          ...(index === 0 && {
            nextBtnText: 'Vamos!',
          }),
        },
      })),
      onDestroyStarted: () => {
        // Only mark as done if user completed the tour (clicked last button)
        if (driverInstance.isLastStep()) {
          localStorage.setItem(STORAGE_KEYS.TOUR_DONE, 'true');
          localStorage.removeItem(STORAGE_KEYS.SHOW_TOUR);
          driverInstance.destroy();
          router.push('/accounts');
        } else {
          // User closed early - just destroy, don't mark as done
          driverInstance.destroy();
        }
      },
    });

    driverRef.current = driverInstance;
    driverInstance.drive();
  }, [router]);

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
