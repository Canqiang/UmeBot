// frontend/src/components/MarkdownMessage.tsx
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';
import { CheckCircle, AlertCircle, Info, AlertTriangle, Copy, Check } from 'lucide-react';

interface MarkdownMessageProps {
  content: string;
  className?: string;
}

export const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ content, className = '' }) => {
  const [copiedCode, setCopiedCode] = React.useState<string | null>(null);

  const copyToClipboard = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className={`markdown-body ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex, rehypeHighlight]}
        components={{
        // 标题样式
        h1: ({ children }) => (
          <h1 className="text-2xl font-bold mt-6 mb-4 text-gray-900">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-xl font-semibold mt-5 mb-3 text-gray-800">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-lg font-medium mt-4 mb-2 text-gray-700">{children}</h3>
        ),

        // 段落
        p: ({ children }) => (
          <p className="mb-3 text-gray-700 leading-relaxed">{children}</p>
        ),

        // 强调样式
        strong: ({ children }) => (
          <strong className="font-semibold text-gray-900">{children}</strong>
        ),
        em: ({ children }) => (
          <em className="italic text-gray-700">{children}</em>
        ),

        // 链接
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 underline"
          >
            {children}
          </a>
        ),

        // 列表
        ul: ({ children }) => (
          <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>
        ),
        li: ({ children }) => (
          <li className="text-gray-700">
            <span className="ml-2">{children}</span>
          </li>
        ),

        // 引用块
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-3 bg-blue-50 rounded-r">
            <div className="text-gray-700 italic">{children}</div>
          </blockquote>
        ),

        // 代码块
        code: ({ inline, className, children, ...props }: {inline?: boolean; className?: string; children: React.ReactNode}) => {
          const match = /language-(\w+)/.exec(className || '');
          const codeString = String(children).replace(/\n$/, '');
          const codeId = `code-${Math.random().toString(36).substr(2, 9)}`;

          if (!inline && match) {
            return (
              <div className="relative group my-3">
                <div className="absolute top-0 right-0 flex items-center space-x-2 p-2">
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {match[1]}
                  </span>
                  <button
                    onClick={() => copyToClipboard(codeString, codeId)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-200 rounded"
                    title="复制代码"
                  >
                    {copiedCode === codeId ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4 text-gray-600" />
                    )}
                  </button>
                </div>
                <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-x-auto">
                  <code className={className} {...props}>
                    {children}
                  </code>
                </pre>
              </div>
            );
          }

          return (
            <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm" {...props}>
              {children}
            </code>
          );
        },

        // 表格
        table: ({ children }) => (
          <div className="overflow-x-auto my-4">
            <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-gray-50">{children}</thead>
        ),
        tbody: ({ children }) => (
          <tbody className="bg-white divide-y divide-gray-200">{children}</tbody>
        ),
        tr: ({ children }) => (
          <tr className="hover:bg-gray-50">{children}</tr>
        ),
        th: ({ children }) => (
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-700">
            {children}
          </td>
        ),

        // 水平分割线
        hr: () => (
          <hr className="my-4 border-gray-200" />
        ),

        // 图片
        img: ({ src, alt }) => (
          <img
            src={src}
            alt={alt}
            className="max-w-full h-auto rounded-lg shadow-sm my-3"
          />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
    </div>
  );
};

// ===== 自定义Alert组件 =====
interface AlertProps {
  type: 'info' | 'success' | 'warning' | 'error';
  children: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({ type, children }) => {
  const configs = {
    info: {
      icon: <Info className="w-5 h-5" />,
      className: 'bg-blue-50 border-blue-200 text-blue-800',
      iconClass: 'text-blue-500'
    },
    success: {
      icon: <CheckCircle className="w-5 h-5" />,
      className: 'bg-green-50 border-green-200 text-green-800',
      iconClass: 'text-green-500'
    },
    warning: {
      icon: <AlertTriangle className="w-5 h-5" />,
      className: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      iconClass: 'text-yellow-500'
    },
    error: {
      icon: <AlertCircle className="w-5 h-5" />,
      className: 'bg-red-50 border-red-200 text-red-800',
      iconClass: 'text-red-500'
    }
  };

  const config = configs[type];

  return (
    <div className={`flex items-start p-4 mb-3 border rounded-lg ${config.className}`}>
      <div className={`flex-shrink-0 ${config.iconClass}`}>
        {config.icon}
      </div>
      <div className="ml-3 flex-1">
        {children}
      </div>
    </div>
  );
};