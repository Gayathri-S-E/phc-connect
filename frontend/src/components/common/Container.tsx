import React from 'react';

export const Container: React.FC<React.HTMLAttributes<HTMLDivElement> & { as?: React.ElementType }> = ({
  as: Tag = 'div',
  className = '',
  children,
  ...props
}) => (
  <Tag
    className={`mx-auto w-full max-w-[1280px] px-4 sm:px-6 lg:px-8 min-w-0 ${className}`}
    {...props}
  >
    {children}
  </Tag>
);
