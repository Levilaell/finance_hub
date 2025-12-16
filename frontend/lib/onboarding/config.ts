import type { DriveStep } from 'driver.js';

export const TOUR_STEPS: DriveStep[] = [
  {
    popover: {
      title: 'Bem-vindo ao CaixaHub!',
      description: 'Vamos conectar seu banco para você ver suas finanças em tempo real.',
      side: 'over',
      align: 'center',
    },
  },
  {
    element: '[data-tour="contas"]',
    popover: {
      title: 'Conecte seu banco',
      description: 'É aqui que você conecta sua conta. Seguro, via Open Banking.',
      side: 'top',
      align: 'center',
    },
  },
  {
    popover: {
      title: 'Pronto!',
      description: 'Conecte agora para ver suas transações categorizadas automaticamente.',
      side: 'over',
      align: 'center',
    },
  },
];

export const TOUR_CONFIG = {
  showProgress: true,
  animate: true,
  allowClose: true,
  overlayColor: 'rgba(0, 0, 0, 0.75)',
  stagePadding: 8,
  stageRadius: 8,
  popoverClass: 'caixahub-tour-popover',
  nextBtnText: 'Próximo',
  prevBtnText: 'Anterior',
  doneBtnText: 'Conectar Banco',
};

export const STORAGE_KEYS = {
  SHOW_TOUR: 'caixahub_show_tour',
  TOUR_DONE: 'caixahub_tour_done',
};
