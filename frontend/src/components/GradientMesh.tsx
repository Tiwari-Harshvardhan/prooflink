// Soft, blurred gradient-blob background. Pure CSS, no images — sits
// behind content via absolute positioning with a low z-index. Used
// sparingly, once per page section, so it reads as atmosphere rather
// than noise.
export default function GradientMesh({
  variant = 'hero',
  className = '',
}: {
  variant?: 'hero' | 'quiet'
  className?: string
}) {
  if (variant === 'quiet') {
    return (
      <div className={`absolute inset-0 -z-10 overflow-hidden ${className}`} aria-hidden="true">
        <div className="absolute -top-24 right-[-10%] w-[420px] h-[420px] rounded-full bg-brand-100/60 blur-3xl" />
      </div>
    )
  }

  return (
    <div className={`absolute inset-0 -z-10 overflow-hidden ${className}`} aria-hidden="true">
      <div className="absolute -top-32 -left-24 w-[480px] h-[480px] rounded-full bg-brand-200/50 blur-3xl" />
      <div className="absolute -top-10 right-[-8%] w-[440px] h-[440px] rounded-full bg-violet/25 blur-3xl" />
      <div className="absolute top-64 left-1/3 w-[360px] h-[360px] rounded-full bg-sunset/20 blur-3xl" />
    </div>
  )
}
