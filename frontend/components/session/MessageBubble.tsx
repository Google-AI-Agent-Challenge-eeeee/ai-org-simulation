interface MessageBubbleProps {
  content: string
  isStreaming: boolean
}

export function MessageBubble({ content, isStreaming }: MessageBubbleProps) {
  return (
    <div className="rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-3 text-sm text-zinc-100 leading-relaxed max-w-2xl">
      {content}
      {isStreaming && (
        <span className="inline-block w-0.5 h-4 bg-indigo-400 ml-0.5 animate-pulse align-middle" />
      )}
    </div>
  )
}
