import { ReactNode } from 'react';
import clsx from 'clsx';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-medium',
        {
          // Variants
          'bg-surface-2 text-text-dim border border-border': variant === 'default',
          'bg-success/20 text-success border border-success/30': variant === 'success',
          'bg-warning/20 text-warning border border-warning/30': variant === 'warning',
          'bg-error/20 text-error border border-error/30': variant === 'error',
          'bg-accent/20 text-accent border border-accent/30': variant === 'info',

          // Sizes
          'px-2 py-0.5 text-xs': size === 'sm',
          'px-3 py-1 text-sm': size === 'md',
        },
        className
      )}
    >
      {children}
    </span>
  );
}
