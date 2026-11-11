import React, { useState } from 'react';
import {
  Copy,
  Check,
  Bookmark,
  Volume2,
  BookOpen,
  Terminal,
} from 'lucide-react';
import { MathRenderer } from './MathRenderer';
import { ConceptDiagram } from './ConceptDiagram';
import { MessageCitation } from '../types';

interface TutorResponseProps {
  content: string;
  citations?: MessageCitation[];
  onPlayAudio?: () => void;
}

export const TutorResponse: React.FC<TutorResponseProps> = ({
  content,
  citations,
  onPlayAudio,
}) => {
  const [copied, setCopied] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [copiedCodeIndex, setCopiedCodeIndex] = useState<number | null>(null);

  const handleCopyAnswer = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyCode = (code: string, index: number) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeIndex(index);
    setTimeout(() => setCopiedCodeIndex(null), 2000);
  };

  /**
   * Helper to parse inline markdown formatting (**bold**, *italic*, `code`, [link](url))
   */
  const renderInlineFormatting = (text: string, keyPrefix: number) => {
    const tokens = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g);
    return tokens.map((tok, i) => {
      if (tok.startsWith('**') && tok.endsWith('**') && tok.length > 4) {
        return <strong key={`${keyPrefix}-${i}`} className="font-semibold text-slate-900">{tok.slice(2, -2)}</strong>;
      }
      if (tok.startsWith('*') && tok.endsWith('*') && tok.length > 2) {
        return <em key={`${keyPrefix}-${i}`}>{tok.slice(1, -1)}</em>;
      }
      if (tok.startsWith('`') && tok.endsWith('`') && tok.length > 2) {
        return (
          <code key={`${keyPrefix}-${i}`} className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-800 font-mono text-[0.85em]">
            {tok.slice(1, -1)}
          </code>
        );
      }
      const linkMatch = tok.match(/^\[([^\]]+)\]\((https?:\/\/[^)]+)\)$/);
      if (linkMatch) {
        return (
          <a
            key={`${keyPrefix}-${i}`}
            href={linkMatch[2]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sky-600 hover:underline font-medium"
          >
            {linkMatch[1]}
          </a>
        );
      }
      return <span key={`${keyPrefix}-${i}`}>{tok}</span>;
    });
  };

  /**
   * Helper to parse markdown math delimiters ($...$, $$...$$) and inline markdown within text
   */
  const renderMathAndText = (text: string) => {
    const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('$$') && part.endsWith('$$')) {
        return <MathRenderer key={idx} math={part.slice(2, -2).trim()} block={true} />;
      } else if (part.startsWith('$') && part.endsWith('$')) {
        return <MathRenderer key={idx} math={part.slice(1, -1).trim()} block={false} />;
      }
      return <React.Fragment key={idx}>{renderInlineFormatting(part, idx)}</React.Fragment>;
    });
  };

  /**
   * Structured Parser for Markdown blocks:
   * - Code blocks & diagrams: ```lang ... ```
   * - Tables: | col1 | col2 |
   * - Headings: #, ##, ###
   * - Bullet & Numbered lists: *, -, 1.
   * - Standard paragraphs
   */
  const renderParsedContent = () => {
    const lines = content.split('\n');
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeLanguage = '';
    let codeLines: string[] = [];
    let inTable = false;
    let tableRows: string[][] = [];
    let codeBlockCount = 0;

    const flushCodeBlock = () => {
      const codeText = codeLines.join('\n');
      const currentIndex = codeBlockCount++;

      if (codeLanguage.trim().toLowerCase() === 'diagram') {
        elements.push(<ConceptDiagram key={`diagram-${currentIndex}`} type={codeText} />);
      } else {
        elements.push(
          <div key={`code-${currentIndex}`} className="my-3 rounded-2xl overflow-hidden border border-slate-700 bg-slate-900 shadow-md">
            <div className="bg-slate-800 px-4 py-1.5 flex items-center justify-between text-xs text-slate-300 border-b border-slate-700">
              <span className="flex items-center gap-1.5 font-mono text-[11px] text-sky-400">
                <Terminal className="w-3.5 h-3.5" />
                {codeLanguage || 'code'}
              </span>
              <button
                onClick={() => handleCopyCode(codeText, currentIndex)}
                className="flex items-center gap-1 text-[11px] hover:text-white transition-colors"
              >
                {copiedCodeIndex === currentIndex ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy code</span>
                  </>
                )}
              </button>
            </div>
            <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed">
              <code>{codeText}</code>
            </pre>
          </div>
        );
      }
      codeLines = [];
      inCodeBlock = false;
      codeLanguage = '';
    };

    const flushTable = () => {
      if (tableRows.length === 0) return;
      const headers = tableRows[0];
      const rows = tableRows.slice(1);
      elements.push(
        <div key={`table-${elements.length}`} className="my-3 overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50">
              <tr>
                {headers.map((h, i) => (
                  <th key={i} className="px-3 py-2 text-left font-bold text-slate-700 uppercase tracking-wider">
                    {renderMathAndText(h.trim())}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-100">
              {rows.map((row, rIdx) => (
                <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="px-3 py-2 text-slate-700">
                      {renderMathAndText(cell.trim())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
      inTable = false;
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Code block delimiters
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          flushCodeBlock();
        } else {
          if (inTable) flushTable();
          inCodeBlock = true;
          codeLanguage = line.trim().slice(3).trim();
        }
        continue;
      }

      if (inCodeBlock) {
        codeLines.push(line);
        continue;
      }

      // Markdown Tables (| cell | cell |)
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        // Skip separator line (e.g. |---|---|)
        if (line.includes('---')) {
          continue;
        }
        const cells = line.split('|').slice(1, -1);
        tableRows.push(cells);
        inTable = true;
        continue;
      } else if (inTable) {
        flushTable();
      }

      // Headings
      if (line.startsWith('### ')) {
        elements.push(
          <h4 key={i} className="font-bold text-sm text-slate-900 mt-3 mb-1">
            {renderMathAndText(line.replace('### ', ''))}
          </h4>
        );
      } else if (line.startsWith('## ')) {
        elements.push(
          <h3 key={i} className="font-bold text-base text-slate-900 mt-4 mb-1.5 border-b border-slate-100 pb-1">
            {renderMathAndText(line.replace('## ', ''))}
          </h3>
        );
      } else if (line.startsWith('# ')) {
        elements.push(
          <h2 key={i} className="font-extrabold text-lg text-slate-900 mt-4 mb-2">
            {renderMathAndText(line.replace('# ', ''))}
          </h2>
        );
      }
      // Bullet lists
      else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        elements.push(
          <li key={i} className="ml-4 list-disc text-slate-700 text-xs sm:text-sm my-0.5 leading-relaxed">
            {renderMathAndText(line.trim().slice(2))}
          </li>
        );
      }
      // Numbered lists
      else if (/^\d+\.\s/.test(line.trim())) {
        const textPart = line.trim().replace(/^\d+\.\s/, '');
        elements.push(
          <li key={i} className="ml-4 list-decimal text-slate-700 text-xs sm:text-sm my-0.5 leading-relaxed">
            {renderMathAndText(textPart)}
          </li>
        );
      }
      // Empty lines (headings & paragraphs manage their own vertical margins)
      else if (!line.trim()) {
        continue;
      }
      // Standard Paragraph
      else {
        elements.push(
          <p key={i} className="text-xs sm:text-sm text-slate-700 leading-relaxed my-1">
            {renderMathAndText(line)}
          </p>
        );
      }
    }

    if (inCodeBlock) flushCodeBlock();
    if (inTable) flushTable();

    return elements;
  };

  return (
    <div className="flex flex-col space-y-3">
      {/* Formatted Content */}
      <div className="prose prose-sm max-w-none text-slate-800">
        {renderParsedContent()}
      </div>

      {/* Citations & Source References */}
      {citations && citations.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-col gap-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <BookOpen className="w-3 h-3 text-sky-600" />
            Verified Curriculum References
          </span>
          <div className="flex flex-wrap gap-2">
            {citations.map((cite, idx) => (
              <div
                key={idx}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-sky-50 border border-sky-100 text-[11px] text-sky-800"
                title={cite.excerpt || cite.chapter}
              >
                <span className="font-semibold">{cite.source_name}</span>
                <span className="text-sky-500">•</span>
                <span>{cite.chapter}</span>
                {cite.page_number && <span className="text-sky-600 font-medium">(p. {cite.page_number})</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Answer Actions Toolbar */}
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          {onPlayAudio && (
            <button
              onClick={onPlayAudio}
              className="p-1.5 hover:text-sky-600 hover:bg-slate-100 rounded-lg transition-colors flex items-center gap-1 font-medium text-[11px]"
              title="Listen to this explanation"
            >
              <Volume2 className="w-3.5 h-3.5 text-sky-600" />
              <span>Listen</span>
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setBookmarked(!bookmarked)}
            className={`p-1.5 rounded-lg transition-colors flex items-center gap-1 font-medium text-[11px] ${
              bookmarked ? 'text-amber-600 bg-amber-50' : 'hover:text-slate-700 hover:bg-slate-100'
            }`}
            title={bookmarked ? 'Saved to bookmarks' : 'Save answer'}
          >
            <Bookmark className="w-3.5 h-3.5" />
            <span>{bookmarked ? 'Saved' : 'Save'}</span>
          </button>

          <button
            onClick={handleCopyAnswer}
            className="p-1.5 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors flex items-center gap-1 font-medium text-[11px]"
            title="Copy entire explanation"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-600">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

