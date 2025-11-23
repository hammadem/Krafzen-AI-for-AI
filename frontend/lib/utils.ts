import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Function to merge two strings usable in css classess merging
export function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
};

export function formatDate(dateString: string) {
  const date = new Date(dateString);

  const day = date.getDate();
  const month = date.toLocaleString('en-US', { month: 'short' });
  const year = date.getFullYear();

  // suffix
  const suffix =
    day % 10 === 1 && day !== 11 ? "st" :
      day % 10 === 2 && day !== 12 ? "nd" :
        day % 10 === 3 && day !== 13 ? "rd" : "th";

  return `${day}${suffix} ${month}. ${year}`;
}

export function formatTime(dateString: string) {
  return new Date(dateString).toLocaleTimeString('en-US', {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  });
}
