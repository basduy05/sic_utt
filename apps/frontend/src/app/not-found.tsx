import Link from 'next/link';
import { ArrowLeft, AlertCircle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-3xl bg-amber-100 text-amber-700 flex items-center justify-center mb-4 shadow-md">
        <AlertCircle size={32} />
      </div>
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Không Tìm Thấy Trang (404)</h2>
      <p className="text-sm text-slate-500 max-w-md mb-6">
        Trang bạn đang truy cập không tồn tại hoặc đã được di chuyển.
      </p>
      <Link
        href="/chat"
        className="flex items-center space-x-2 px-5 py-2.5 rounded-2xl bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow-md transition hover:scale-105"
      >
        <ArrowLeft size={16} />
        <span>Quay về phòng khám AI</span>
      </Link>
    </div>
  );
}
