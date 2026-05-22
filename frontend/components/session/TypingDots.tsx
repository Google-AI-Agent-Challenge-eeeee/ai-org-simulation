export function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-3 py-2 rounded-xl bg-zinc-800 w-fit">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-zinc-400 animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  )
}
