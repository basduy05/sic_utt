export function formatTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

export function getStatusColorClass(status: string): string {
  switch (status) {
    case 'CRITICAL_HIGH':
    case 'CRITICAL_LOW':
      return 'bg-red-100 text-red-700 border-red-300 animate-pulse';
    case 'HIGH':
    case 'LOW':
      return 'bg-amber-100 text-amber-800 border-amber-300';
    case 'NORMAL':
    default:
      return 'bg-emerald-100 text-emerald-800 border-emerald-300';
  }
}
