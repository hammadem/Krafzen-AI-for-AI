import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Function to merge two strings usable in css classess merging
export function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
};