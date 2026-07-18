import * as React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary';
}

const variants = {
  default: 'bg-slate-900 text-white hover:bg-slate-700',
  secondary: 'bg-white text-slate-900 border border-slate-200 hover:bg-slate-50',
};

export function Button({ className = '', variant = 'default', ...props }: ButtonProps) {
  return (
    <button className={`${variants[variant]} inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition ${className}`} {...props} />
  );
}
