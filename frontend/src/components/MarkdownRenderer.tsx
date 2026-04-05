'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface MarkdownRendererProps {
  content: string
  className?: string
  darkMode?: boolean
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = '',
  darkMode = false
}) => {
  return (
    <div className={`markdown-renderer ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, className, children, ...props }) {
            const inline = !className || !/language-(\w+)/.test(className)
            const match = /language-(\w+)/.exec(className || '')
            const language = match ? match[1] : ''

            if (!inline && match) {
              return (
                <div className="my-4 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-800">
                  <div className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-xs font-medium text-gray-600 dark:text-gray-300">
                    {language}
                  </div>
                  <SyntaxHighlighter
                    style={(darkMode ? vscDarkPlus : vs) as any}
                    language={language}
                    PreTag="div"
                    customStyle={{
                      margin: 0,
                      borderRadius: 0,
                      padding: '1rem'
                    } as any}
                    {...(props as any)}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                </div>
              )
            }

            return (
              <code
                className={`inline-code px-1.5 py-0.5 rounded text-sm bg-gray-100 dark:bg-gray-800 ${className}`}
                {...props}
              >
                {children}
              </code>
            )
          },
          table({ children }) {
            return (
              <div className="my-4 overflow-x-auto">
                <table className="w-full text-sm text-left border-collapse">
                  {children}
                </table>
              </div>
            )
          },
          thead({ children }) {
            return (
              <thead className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white font-semibold">
                {children}
              </thead>
            )
          },
          tbody({ children }) {
            return <tbody className="divide-y divide-gray-200 dark:divide-gray-700">{children}</tbody>
          },
          tr({ children }) {
            return <tr className="hover:bg-gray-50 dark:hover:bg-gray-800">{children}</tr>
          },
          th({ children }) {
            return <th className="px-4 py-2 border">{children}</th>
          },
          td({ children }) {
            return <td className="px-4 py-2 border">{children}</td>
          },
          a({ children, href, ...props }) {
            return (
              <a
                href={href}
                target={href?.startsWith('http') ? '_blank' : '_self'}
                rel={href?.startsWith('http') ? 'noopener noreferrer' : ''}
                className="text-blue-600 dark:text-blue-400 hover:underline"
                {...props}
              >
                {children}
                {href?.startsWith('http') && (
                  <span className="ml-1 text-xs opacity-70">↗</span>
                )}
              </a>
            )
          },
          h1({ children }) {
            return <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">{children}</h1>
          },
          h2({ children }) {
            return <h2 className="text-2xl font-semibold mt-8 mb-4 text-gray-900 dark:text-white">{children}</h2>
          },
          h3({ children }) {
            return <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-900 dark:text-white">{children}</h3>
          },
          h4({ children }) {
            return <h4 className="text-lg font-medium mt-4 mb-2 text-gray-900 dark:text-white">{children}</h4>
          },
          p({ children }) {
            return <p className="mb-4 text-gray-700 dark:text-gray-300 leading-relaxed">{children}</p>
          },
          ul({ children }) {
            return <ul className="mb-4 pl-6 list-disc text-gray-700 dark:text-gray-300">{children}</ul>
          },
          ol({ children }) {
            return <ol className="mb-4 pl-6 list-decimal text-gray-700 dark:text-gray-300">{children}</ol>
          },
          li({ children }) {
            return <li className="mb-1 leading-relaxed">{children}</li>
          },
          blockquote({ children }) {
            return (
              <blockquote className="my-4 p-4 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-gray-700 dark:text-gray-300">
                {children}
              </blockquote>
            )
          },
          hr() {
            return <hr className="my-8 border-gray-200 dark:border-gray-700" />
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownRenderer