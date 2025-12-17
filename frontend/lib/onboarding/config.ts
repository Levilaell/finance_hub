import type { DriveStep } from 'driver.js';

// Desktop steps (lg and above - sidebar always visible)
export const DESKTOP_TOUR_STEPS: DriveStep[] = [
  {
    popover: {
      title: 'Bem-vindo ao CaixaHub!',
      description: 'Vamos conectar seu banco para você ver suas finanças em tempo real.',
      side: 'over',
      align: 'center',
    },
  },
  {
    element: '[data-tour="contas-desktop"]',
    popover: {
      title: 'Contas Bancárias',
      description: 'Clique aqui para acessar a página de contas bancárias.',
      side: 'right',
      align: 'start',
    },
  },
  {
    element: '[data-tour="conectar-banco"]',
    popover: {
      title: 'Conecte seu banco',
      description: 'Clique neste botão para conectar sua conta. Seguro, via Open Banking.',
      side: 'bottom',
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

// Mobile steps (below lg - sidebar is collapsed)
export const MOBILE_TOUR_STEPS: DriveStep[] = [
  {
    popover: {
      title: 'Bem-vindo ao CaixaHub!',
      description: 'Vamos conectar seu banco para você ver suas finanças em tempo real.',
      side: 'over',
      align: 'center',
    },
  },
  {
    element: '[data-tour="menu-mobile"]',
    popover: {
      title: 'Menu de Navegação',
      description: 'Toque aqui para abrir o menu e acessar todas as funcionalidades.',
      side: 'bottom',
      align: 'start',
    },
  },
  {
    element: '[data-tour="contas-mobile"]',
    popover: {
      title: 'Contas Bancárias',
      description: 'Aqui você acessa suas contas bancárias conectadas.',
      side: 'right',
      align: 'start',
    },
  },
  {
    element: '[data-tour="conectar-banco"]',
    popover: {
      title: 'Conecte seu banco',
      description: 'Clique neste botão para conectar sua conta. Seguro, via Open Banking.',
      side: 'bottom',
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

// Breakpoint for lg screens (matches Tailwind's lg)
export const LG_BREAKPOINT = 1024;
