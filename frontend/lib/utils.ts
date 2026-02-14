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

const convertGroupToHistory = (item: ProjectDetails, grouped: HistoryData[]) => {
  const isoDate = item.created_at.split("T")[0];        // 2025-11-16
  const displayDate = formatDate(item.created_at);      // 16th Nov 2025
  const displayTime = formatTime(item.created_at);      // 07:21 PM

  let group = grouped.find(g => g.iso === isoDate);

  if (!group) {
    group = {
      iso: isoDate,
      date: displayDate,
      searches: []
    };
    grouped.push(group);
  }

  group.searches.push({
    title: item.input_text,
    time: displayTime,
    isoTime: item.created_at,   // <-- Add raw timestamp for time sorting
    chats: item?.dxf_url,
    id: item?.id
  });

  // Sort groups by date (newest → oldest)
  grouped.sort((a, b) =>
    new Date(b.iso).getTime() - new Date(a.iso).getTime()
  );
  // Sort searches *inside each day* by newest time first
  grouped.forEach(group => {
    group.searches.sort((a, b) =>
      new Date(b.isoTime).getTime() - new Date(a.isoTime).getTime()
    );
  }
  )
};

export const organizeProjectsAsHistory = ({ projects }: { projects: ProjectDetails[] }) => {
  const history = projects;

  const grouped: HistoryData[] = [];
  history.forEach((item: ProjectDetails) => {
    convertGroupToHistory(item, grouped);
  });

  return grouped;
}

