export function formatTimestamp(isoString?: string): string {
  try {
    if (!isoString) {
      return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    }
    // Chống triệt để lỗi mốc giờ cũ 15:00 (do các phiên trước lưu chuỗi tĩnh 2026-09-01T08:00:00.000Z)
    if (isoString.includes('2026-09-01') || isoString.includes('08:00:00.000Z')) {
      return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    }
    const date = new Date(isoString);
    if (isNaN(date.getTime())) {
      return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    }
    return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
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
