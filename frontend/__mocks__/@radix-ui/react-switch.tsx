import React from 'react';

export const Root = React.forwardRef<HTMLButtonElement, any>(
  ({ checked, onCheckedChange, disabled, defaultChecked, children, ...props }, ref) => {
    const [isChecked, setIsChecked] = React.useState(checked ?? defaultChecked ?? false);
    
    React.useEffect(() => {
      if (checked !== undefined) {
        setIsChecked(checked);
      }
    }, [checked]);
    
    const handleClick = () => {
      if (!disabled) {
        const newChecked = !isChecked;
        setIsChecked(newChecked);
        onCheckedChange?.(newChecked);
      }
    };
    
    return (
      <button
        ref={ref}
        role="switch"
        aria-checked={isChecked}
        data-state={isChecked ? 'checked' : 'unchecked'}
        disabled={disabled}
        onClick={handleClick}
        type="button"
        {...props}
      >
        {children}
      </button>
    );
  }
);

Root.displayName = 'Switch';

export const Thumb = React.forwardRef<HTMLSpanElement, any>(
  (props, ref) => {
    return <span ref={ref} {...props} />;
  }
);

Thumb.displayName = 'SwitchThumb';