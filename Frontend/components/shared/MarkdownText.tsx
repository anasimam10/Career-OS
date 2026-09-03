import React from "react"

interface MarkdownTextProps {
  content: string
  className?: string
}

/**
 * Parses inline markdown tokens: bold, italic, code, and links.
 */
function renderInline(text: string): React.ReactNode[] {
  // Regex to match markdown links: [text](url), bold: **bold**, code: `code`
  const regex = /(\[.*?\]\(.*?\)|\*\*.*?\*\*|`.*?`|\*.*?\*)/g
  const parts = text.split(regex)

  return parts.map((part, index) => {
    if (!part) return null

    // Link: [text](url)
    const linkMatch = part.match(/^\[(.*?)\]\((.*?)\)$/)
    if (linkMatch) {
      const [, label, href] = linkMatch
      return (
        <a
          key={index}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-600 underline font-medium hover:text-indigo-800 transition-colors"
        >
          {label}
        </a>
      )
    }

    // Bold: **text**
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      return (
        <strong key={index} className="font-semibold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      )
    }

    // Code: `code`
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return (
        <code
          key={index}
          className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[11px] text-slate-800"
        >
          {part.slice(1, -1)}
        </code>
      )
    }

    // Italic: *text*
    if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
      return (
        <em key={index} className="italic text-slate-700">
          {part.slice(1, -1)}
        </em>
      )
    }

    return <span key={index}>{part}</span>
  })
}

/**
 * High quality zero-dependency semantic Markdown renderer for Coach / Mentor dialogue.
 */
export function MarkdownText({ content, className = "" }: MarkdownTextProps) {
  if (!content) return null

  const lines = content.split("\n")
  const elements: React.ReactNode[] = []
  let currentList: { type: "ul" | "ol"; items: string[] } | null = null

  const flushList = () => {
    if (!currentList) return
    const listIndex = elements.length
    if (currentList.type === "ul") {
      elements.push(
        <ul key={`ul-${listIndex}`} className="my-2 ml-4 list-disc space-y-1 text-xs sm:text-sm text-slate-700">
          {currentList.items.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ul>
      )
    } else {
      elements.push(
        <ol key={`ol-${listIndex}`} className="my-2 ml-4 list-decimal space-y-1 text-xs sm:text-sm text-slate-700">
          {currentList.items.map((item, idx) => (
            <li key={idx} className="leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ol>
      )
    }
    currentList = null
  }

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i]
    const trimmed = rawLine.trim()

    if (!trimmed) {
      flushList()
      continue
    }

    // Headings
    if (trimmed.startsWith("### ")) {
      flushList()
      elements.push(
        <h4 key={i} className="mt-3 mb-1 text-sm font-bold text-slate-900 tracking-tight">
          {renderInline(trimmed.slice(4))}
        </h4>
      )
      continue
    }

    if (trimmed.startsWith("## ")) {
      flushList()
      elements.push(
        <h3 key={i} className="mt-4 mb-1.5 text-base font-bold text-slate-900 tracking-tight">
          {renderInline(trimmed.slice(3))}
        </h3>
      )
      continue
    }

    if (trimmed.startsWith("# ")) {
      flushList()
      elements.push(
        <h2 key={i} className="mt-4 mb-2 text-lg font-bold text-slate-900 tracking-tight">
          {renderInline(trimmed.slice(2))}
        </h2>
      )
      continue
    }

    // Bullet lists (* or -)
    const bulletMatch = trimmed.match(/^[-*]\s+(.*)$/)
    if (bulletMatch) {
      if (!currentList || currentList.type !== "ul") {
        flushList()
        currentList = { type: "ul", items: [] }
      }
      currentList.items.push(bulletMatch[1])
      continue
    }

    // Numbered lists (1. 2. etc)
    const numMatch = trimmed.match(/^\d+\.\s+(.*)$/)
    if (numMatch) {
      if (!currentList || currentList.type !== "ol") {
        flushList()
        currentList = { type: "ol", items: [] }
      }
      currentList.items.push(numMatch[1])
      continue
    }

    // Regular paragraph
    flushList()
    elements.push(
      <p key={i} className="my-1.5 text-xs sm:text-sm text-slate-700 leading-relaxed">
        {renderInline(trimmed)}
      </p>
    )
  }

  flushList()

  return <div className={`space-y-1 ${className}`}>{elements}</div>
}
