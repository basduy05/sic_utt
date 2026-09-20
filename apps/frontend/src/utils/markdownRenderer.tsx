import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  ShieldAlert,
  CheckCircle,
  AlertTriangle,
  Info,
  Stethoscope,
  Sparkles,
  ChevronDown,
  Activity,
  Cpu,
  GitCompare,
  ArrowRight,
  ShieldCheck,
  Microscope,
  HelpCircle
} from 'lucide-react';

export const ClinicalThinkingAccordion: React.FC<{ thinking: string; isStreaming?: boolean }> = ({
  thinking,
  isStreaming = false,
}) => {
  const [isOpen, setIsOpen] = useState(isStreaming);

  useEffect(() => {
    if (isStreaming) {
      setIsOpen(true);
    }
  }, [isStreaming]);

  // Nhóm các dòng suy luận thành các phần mục lâm sàng
  const lines = thinking.split('\n').map((l) => l.trim()).filter(Boolean);
  const items: { label: string; value: string; type: 'patho' | 'diff' | 'red_flag' | 'next' | 'general' }[] = [];

  lines.forEach((l) => {
    const clean = l.replace(/^[-*•]\s*/, '').trim();
    if (!clean) return;

    const colonIdx = clean.indexOf(':');
    if (colonIdx > 0 && colonIdx < 60) {
      const label = clean.substring(0, colonIdx).trim();
      const val = clean.substring(colonIdx + 1).trim();
      const lower = label.toLowerCase();
      let type: 'patho' | 'diff' | 'red_flag' | 'next' | 'general' = 'general';

      if (lower.includes('cơ chế') || lower.includes('bệnh sinh') || lower.includes('triệu chứng')) {
        type = 'patho';
      } else if (lower.includes('phân biệt') || lower.includes('loại trừ') || lower.includes('phản biện')) {
        type = 'diff';
      } else if (lower.includes('cờ đỏ') || lower.includes('red flag') || lower.includes('cảnh báo') || lower.includes('an toàn')) {
        type = 'red_flag';
      } else if (lower.includes('định hướng') || lower.includes('tiếp theo') || lower.includes('cận lâm sàng') || lower.includes('tư vấn')) {
        type = 'next';
      }

      items.push({ label, value: val, type });
    } else {
      if (items.length > 0) {
        items[items.length - 1].value += ' ' + clean;
      } else {
        items.push({ label: 'Biện chứng lâm sàng', value: clean, type: 'general' });
      }
    }
  });

  return (
    <div className="my-2.5 rounded-2xl border border-teal-200/90 bg-gradient-to-br from-teal-50/50 via-white to-cyan-50/40 overflow-hidden shadow-2xs transition-all">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between text-left hover:bg-teal-50/60 transition cursor-pointer select-none"
      >
        <div className="flex items-center space-x-2">
          <span className="p-1 rounded-lg bg-teal-100/90 text-teal-700 shadow-2xs">
            <Microscope className="w-3.5 h-3.5" />
          </span>
          <span className="text-xs font-bold text-slate-800 tracking-tight flex items-center gap-1.5">
            Quy trình Suy luận Lâm sàng (Clinical Chain-of-Thought)
            {isStreaming && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-amber-100 text-amber-800 animate-pulse">
                <Sparkles size={10} /> Đang biện luận...
              </span>
            )}
          </span>
          <span className="hidden sm:inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-teal-100/70 text-teal-800 border border-teal-200/60">
            {items.length > 0 ? `${items.length} bước biện chứng` : 'Biện chứng y khoa'}
          </span>
        </div>
        <div className="flex items-center space-x-1.5 text-xs text-slate-400">
          <span className="text-[11px] font-medium text-teal-700/90">
            {isOpen ? 'Thu gọn' : 'Xem chi tiết'}
          </span>
          <ChevronDown
            className={`w-3.5 h-3.5 text-teal-600 transition-transform duration-200 ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </div>
      </button>

      {isOpen && (
        <div className="px-3.5 pb-3.5 pt-1.5 border-t border-teal-100/80 space-y-2.5 text-xs text-slate-700 animate-in fade-in duration-200">
          {items.map((item, i) => {
            const isPatho = item.type === 'patho';
            const isDiff = item.type === 'diff';
            const isRedFlag = item.type === 'red_flag';
            const isNext = item.type === 'next';

            return (
              <div
                key={i}
                className={`p-2.5 rounded-xl border text-xs leading-relaxed transition-all ${
                  isPatho
                    ? 'bg-indigo-50/40 border-indigo-200/80 text-indigo-950'
                    : isDiff
                    ? 'bg-cyan-50/40 border-cyan-200/80 text-cyan-950'
                    : isRedFlag
                    ? 'bg-rose-50/50 border-rose-200/90 text-rose-950'
                    : isNext
                    ? 'bg-emerald-50/40 border-emerald-200/80 text-emerald-950'
                    : 'bg-white border-slate-200 text-slate-800'
                }`}
              >
                <div className="flex items-start gap-2">
                  <span className="mt-0.5 flex-shrink-0">
                    {isPatho ? (
                      <Stethoscope className="w-3.5 h-3.5 text-indigo-600" />
                    ) : isDiff ? (
                      <GitCompare className="w-3.5 h-3.5 text-cyan-600" />
                    ) : isRedFlag ? (
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-600 animate-pulse" />
                    ) : isNext ? (
                      <ArrowRight className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <CheckCircle className="w-3.5 h-3.5 text-teal-600" />
                    )}
                  </span>
                  <div className="flex-1">
                    <strong
                      className={`font-semibold tracking-tight mr-1 ${
                        isPatho
                          ? 'text-indigo-900'
                          : isDiff
                          ? 'text-cyan-900'
                          : isRedFlag
                          ? 'text-rose-900 font-bold'
                          : isNext
                          ? 'text-emerald-900'
                          : 'text-slate-900'
                      }`}
                    >
                      {item.label}:
                    </strong>
                    <span className="text-slate-700">
                      {renderInlineMarkdown(item.value)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

/**
 * Phân tích cú pháp inline markdown: **in đậm**, *nghiêng*, `code`, và văn bản thông thường
 */
export function renderInlineMarkdown(text: string): React.ReactNode[] {
  if (!text) return [];

  // Tokenize theo các mẫu markdown: `code`, **bold**, *italic*, _italic_
  const tokens: React.ReactNode[] = [];
  const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_)/g;
  
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    // Phần văn bản thường trước match
    if (match.index > lastIndex) {
      tokens.push(text.substring(lastIndex, match.index));
    }

    const tokenText = match[0];

    if (tokenText.startsWith('`') && tokenText.endsWith('`')) {
      // Code / ICD-10 Tag
      const codeVal = tokenText.slice(1, -1);
      tokens.push(
        <code
          key={match.index}
          className="px-1.5 py-0.5 mx-0.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200/80 font-mono text-[11px] font-bold shadow-xs inline-block"
        >
          {codeVal}
        </code>
      );
    } else if (tokenText.startsWith('**') && tokenText.endsWith('**')) {
      // Bold Text
      const boldVal = tokenText.slice(2, -2);
      tokens.push(
        <strong key={match.index} className="font-bold text-slate-900 text-teal-950">
          {boldVal}
        </strong>
      );
    } else if ((tokenText.startsWith('*') && tokenText.endsWith('*')) || (tokenText.startsWith('_') && tokenText.endsWith('_'))) {
      // Italic Text
      const italicVal = tokenText.slice(1, -1);
      tokens.push(
        <em key={match.index} className="italic text-slate-600">
          {italicVal}
        </em>
      );
    }

    lastIndex = match.index + tokenText.length;
  }

  if (lastIndex < text.length) {
    tokens.push(text.substring(lastIndex));
  }

  return tokens;
}

/**
 * Render khối văn bản Markdown đầy đủ cho tin nhắn và Bệnh án lâm sàng
 */
export function renderRichMarkdown(content: string, isRecordMode = false): React.ReactNode {
  if (!content) return null;

  // Tách khối suy luận lâm sàng <clinical_thinking>...</clinical_thinking> (kể cả khi đang stream chưa đóng thẻ)
  let thinkingContent: string | null = null;
  let isThinkingStreaming = false;
  let mainText = content;

  // 1. Kiểm tra cặp thẻ đã đóng hoàn chỉnh
  const closedMatch = content.match(/<clinical_thinking[\s\S]*?>([\s\S]*?)<\/clinical_thinking>/i);
  if (closedMatch) {
    thinkingContent = closedMatch[1].trim();
    mainText = content.replace(/<clinical_thinking[\s\S]*?>[\s\S]*?<\/clinical_thinking>/i, '').trim();
  } else {
    // 2. Kiểm tra thẻ mở đang stream chưa kịp đóng
    const openMatch = content.match(/<clinical_thinking[\s\S]*?>([\s\S]*)/i);
    if (openMatch) {
      thinkingContent = openMatch[1].trim();
      isThinkingStreaming = true;
      mainText = content.replace(/<clinical_thinking[\s\S]*?>[\s\S]*/i, '').trim();
    }
  }

  // Loại bỏ triệt để bất kỳ thẻ rác nào sót lại để không bao giờ bị lỗi hiển thị thô
  mainText = mainText.replace(/<\/?clinical_thinking[\s\S]*?>/gi, '').trim();

  const lines = mainText.split('\n');
  const renderedElements: React.ReactNode[] = [];

  let inList = false;
  let listItems: React.ReactNode[] = [];

  const flushList = (key: string | number) => {
    if (inList && listItems.length > 0) {
      renderedElements.push(
        <ul key={`ul-${key}`} className="my-2 space-y-1.5 pl-1">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();

    // 1. Dòng trống
    if (line === '') {
      flushList(idx);
      renderedElements.push(<div key={`empty-${idx}`} className="h-2" />);
      return;
    }

    // 2. Tiêu đề H1 (# ...)
    if (line.startsWith('# ')) {
      flushList(idx);
      const title = line.replace(/^#\s+/, '');
      renderedElements.push(
        <div key={idx} className="my-3 pb-2 border-b-2 border-teal-600 flex items-center space-x-2">
          <Stethoscope className="w-5 h-5 text-teal-600 flex-shrink-0" />
          <h1 className="text-lg md:text-xl font-extrabold text-slate-900 tracking-tight">
            {renderInlineMarkdown(title)}
          </h1>
        </div>
      );
      return;
    }

    // 3. Tiêu đề H2 (## ...)
    if (line.startsWith('## ')) {
      flushList(idx);
      const title = line.replace(/^##\s+/, '');
      renderedElements.push(
        <div key={idx} className="mt-4 mb-2 pt-2 border-t border-slate-200 flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-teal-600 flex-shrink-0" />
          <h2 className="text-base md:text-lg font-bold text-slate-800 tracking-tight uppercase">
            {renderInlineMarkdown(title)}
          </h2>
        </div>
      );
      return;
    }

    // 4. Tiêu đề H3 (### ...)
    if (line.startsWith('### ')) {
      flushList(idx);
      const title = line.replace(/^###\s+/, '');
      renderedElements.push(
        <h3 key={idx} className="mt-3 mb-1 font-bold text-sm md:text-base text-teal-900 flex items-center space-x-1.5">
          <span>{renderInlineMarkdown(title)}</span>
        </h3>
      );
      return;
    }

    // 5. Cảnh báo Đỏ khẩn cấp
    if (line.includes('🚨') || line.includes('BÁO ĐỘNG ĐỎ')) {
      flushList(idx);
      renderedElements.push(
        <div key={idx} className="my-2.5 p-3.5 bg-red-50/90 border-l-4 border-red-500 rounded-r-2xl text-red-950 font-semibold flex items-start space-x-2.5 shadow-xs">
          <ShieldAlert className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5 animate-bounce" />
          <div className="flex-1 text-sm md:text-base leading-relaxed">{renderInlineMarkdown(line.replace(/🚨/g, ''))}</div>
        </div>
      );
      return;
    }

    // 6. Disclaimer Y khoa (⚠️ *Lưu ý: ...)
    if (line.startsWith('⚠️') || line.includes('*Lưu ý: Kết quả trên do Trí tuệ nhân tạo')) {
      flushList(idx);
      renderedElements.push(
        <div key={idx} className="my-3 p-3 bg-amber-50/80 border border-amber-200/90 rounded-xl text-amber-900 text-xs leading-relaxed flex items-start gap-2 shadow-2xs">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">{renderInlineMarkdown(line.replace(/^[⚠️\s*]+/, ''))}</div>
        </div>
      );
      return;
    }

    // 7. Thẻ chẩn đoán bệnh lý đánh số: (1. **Tên bệnh...** (Mã ICD-10...) - Độ tương đồng: ...)
    const numDiagnosisMatch = line.match(/^(\d+)\.\s+(\*\*.*)/);
    if (numDiagnosisMatch) {
      flushList(idx);
      const rank = numDiagnosisMatch[1];
      const rest = numDiagnosisMatch[2];
      renderedElements.push(
        <div key={idx} className="my-2.5 p-3 bg-gradient-to-r from-teal-50/90 to-blue-50/70 border border-teal-200/80 rounded-xl shadow-2xs flex items-start gap-2.5">
          <span className="w-6 h-6 rounded-full bg-teal-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 mt-0.5 shadow-xs">
            {rank}
          </span>
          <div className="flex-1 text-sm md:text-base text-slate-800 leading-relaxed font-medium">
            {renderInlineMarkdown(rest)}
          </div>
        </div>
      );
      return;
    }

    // 8. Trích dẫn phác đồ / Tư vấn lâm sàng (• **Tư vấn...** / • **Phác đồ...**)
    if (line.startsWith('• ') || line.startsWith('&bull; ')) {
      flushList(idx);
      const itemText = line.replace(/^(•|&bull;)\s+/, '');
      renderedElements.push(
        <div key={idx} className="my-1.5 p-2.5 bg-slate-50/90 hover:bg-slate-100/80 border border-slate-200/80 rounded-xl text-xs md:text-sm text-slate-700 leading-relaxed flex items-start gap-2 transition shadow-2xs">
          <BookOpen className="w-3.5 h-3.5 text-teal-600 flex-shrink-0 mt-1" />
          <div className="flex-1">{renderInlineMarkdown(itemText)}</div>
        </div>
      );
      return;
    }

    // 9. Tiêu đề Trích dẫn RAG
    if (line.includes('Trích dẫn Tri Thức') || line.includes('Phác Đồ Bộ Y Tế') || line.includes('RAG Knowledge')) {
      flushList(idx);
      renderedElements.push(
        <div key={idx} className="mt-3.5 mb-1.5 pt-2.5 border-t border-slate-200/80 flex items-center space-x-2 text-teal-800 font-bold text-xs md:text-sm uppercase tracking-wider">
          <BookOpen className="w-4 h-4 text-teal-600" />
          <span>{renderInlineMarkdown(line.replace(/[*📚]/g, ''))}</span>
        </div>
      );
      return;
    }

    // 10. Danh sách không thứ tự (- hoặc *)
    if (line.startsWith('- ') || line.startsWith('* ')) {
      inList = true;
      const itemText = line.substring(2);
      listItems.push(
        <li key={idx} className="flex items-start space-x-2 text-sm md:text-base text-slate-700 leading-relaxed">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-2 flex-shrink-0" />
          <span className="flex-1">{renderInlineMarkdown(itemText)}</span>
        </li>
      );
      return;
    }

    // 11. Dòng thông thường (Paragraph)
    flushList(idx);
    renderedElements.push(
      <p key={idx} className="my-1 text-sm md:text-base text-slate-700 leading-relaxed">
        {renderInlineMarkdown(line)}
      </p>
    );
  });

  flushList('final');
  return (
    <div className="space-y-0.5">
      {thinkingContent && (
        <ClinicalThinkingAccordion
          thinking={thinkingContent}
          isStreaming={isThinkingStreaming}
        />
      )}
      {renderedElements}
    </div>
  );
}
