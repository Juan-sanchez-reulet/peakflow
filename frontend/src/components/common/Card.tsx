import { ReactNode } from 'react';
import clsx from 'clsx';

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'gradient';
  padding?: 'sm' | 'md' | 'lg';
}

export function Card({
  children,
  className,
  variant = 'default',
  padding = 'md',
}: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-xl border',
        {
          'bg-surface border-border': variant === 'default',
          'bg-gradient-accent border-accent/30': variant === 'gradient',

          'p-3': padding === 'sm',
          'p-5': padding === 'md',
          'p-6': padding === 'lg',
        },
        className
      )}
    >
      {children}
    </div>
  );
}
