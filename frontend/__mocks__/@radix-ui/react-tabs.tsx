import React from 'react';

interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | undefined>(undefined);

export const Root = ({ children, defaultValue = 'profile', ...props }: any) => {
  const [value, setValue] = React.useState(defaultValue);
  
  return (
    <TabsContext.Provider value={{ value, onValueChange: setValue }}>
      <div data-orientation="horizontal" {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

export const List = ({ children, ...props }: any) => {
  return (
    <div role="tablist" {...props}>
      {children}
    </div>
  );
};

export const Trigger = ({ children, value: tabValue, ...props }: any) => {
  const context = React.useContext(TabsContext);
  const isActive = context?.value === tabValue;
  
  return (
    <button
      role="tab"
      aria-selected={isActive}
      data-state={isActive ? 'active' : 'inactive'}
      onClick={() => context?.onValueChange(tabValue)}
      type="button"
      {...props}
    >
      {children}
    </button>
  );
};

export const Content = ({ children, value: tabValue, ...props }: any) => {
  const context = React.useContext(TabsContext);
  const isActive = context?.value === tabValue;
  
  if (!isActive) return null;
  
  return (
    <div role="tabpanel" data-state="active" {...props}>
      {children}
    </div>
  );
};