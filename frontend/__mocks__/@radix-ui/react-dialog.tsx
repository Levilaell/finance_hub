import React from 'react';

interface DialogContextValue {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DialogContext = React.createContext<DialogContextValue | undefined>(undefined);

export const Root = ({ children, open, onOpenChange, defaultOpen = false }: any) => {
  const [isOpen, setIsOpen] = React.useState(open ?? defaultOpen);
  
  React.useEffect(() => {
    if (open !== undefined) {
      setIsOpen(open);
    }
  }, [open]);
  
  const handleOpenChange = (newOpen: boolean) => {
    setIsOpen(newOpen);
    onOpenChange?.(newOpen);
  };
  
  return (
    <DialogContext.Provider value={{ open: isOpen, onOpenChange: handleOpenChange }}>
      {children}
    </DialogContext.Provider>
  );
};

export const Trigger = ({ children, ...props }: any) => {
  const context = React.useContext(DialogContext);
  
  return React.cloneElement(children, {
    onClick: () => context?.onOpenChange(true),
    ...props,
  });
};

export const Portal = ({ children }: any) => {
  const context = React.useContext(DialogContext);
  
  if (!context?.open) return null;
  
  return <>{children}</>;
};

export const Overlay = ({ ...props }: any) => {
  return <div data-testid="dialog-overlay" {...props} />;
};

export const Content = ({ children, ...props }: any) => {
  return (
    <div role="dialog" data-testid="dialog-content" {...props}>
      {children}
    </div>
  );
};

export const Header = ({ children, ...props }: any) => {
  return <div {...props}>{children}</div>;
};

export const Footer = ({ children, ...props }: any) => {
  return <div {...props}>{children}</div>;
};

export const Title = ({ children, ...props }: any) => {
  return <h2 {...props}>{children}</h2>;
};

export const Description = ({ children, ...props }: any) => {
  return <p {...props}>{children}</p>;
};

export const Close = ({ children, className, ...props }: any) => {
  const context = React.useContext(DialogContext);
  
  // If children is provided, use it; otherwise provide a button
  if (children) {
    return React.cloneElement(children, {
      onClick: () => context?.onOpenChange(false),
      ...props,
    });
  }
  
  return (
    <button
      className={className}
      onClick={() => context?.onOpenChange(false)}
      type="button"
      {...props}
    >
      <span>×</span>
      <span className="sr-only">Close</span>
    </button>
  );
};