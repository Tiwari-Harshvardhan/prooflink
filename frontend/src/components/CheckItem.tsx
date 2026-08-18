import { Check, X } from 'lucide-react'

export default function CheckItem({ label, passed }: { label: string; passed: boolean }) {
  return (
    <li className="flex items-center gap-3 py-2.5">
      <span
        className={`flex items-center justify-center w-6 h-6 rounded-full shrink-0 ${
          passed ? 'bg-mint/10 text-mint' : 'bg-coral/10 text-coral'
        }`}
      >
        {passed ? <Check className="w-3.5 h-3.5" strokeWidth={3} /> : <X className="w-3.5 h-3.5" strokeWidth={3} />}
      </span>
      <span className="text-sm text-ink-800">{label}</span>
    </li>
  )
}
