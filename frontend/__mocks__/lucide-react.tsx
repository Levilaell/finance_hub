import React from 'react';

// Mock all lucide-react icons as simple spans with the icon name
export const X = (props: any) => <span {...props}>X</span>;

// Export a default function for dynamic imports
const Icon = (props: any) => <span {...props}>Icon</span>;

export default Icon;