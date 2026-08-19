import { useEffect, useState, useCallback } from 'react'
import { api } from '@/services/api'
import { MessageSquare, RefreshCw, Copy, CheckCheck, ExternalLink } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface SmsMessage {
  id: number
  phone_number: string
  message: string
  timestamp: string
  status: string
}

function extractToken(message: string): string | null {
  // Look for ?token= pattern in SMS messages
  const match = message.match(/\?token=([A-Za-z0-9\-_]+)/)
  return match ? match[1] : null
}

function extractOTP(message: string): string | null {
  const match = message.match(/\b(\d{6})\b/)
  return match ? match[1] : null
}

export default function DevSmsInbox() {
  const [messages, setMessages] = useState<SmsMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState<string | null>(null)
  const navigate = useNavigate()

  const loadMessages = useCallback(async () => {
    try {
      const data = await api.getDevSmsInbox()
      setMessages(data.messages || [])
    } catch {
      // Backend might not be running — show empty state
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadMessages()
    // Auto-refresh every 3 seconds
    const interval = setInterval(loadMessages, 3000)
    return () => clearInterval(interval)
  }, [loadMessages])

  function copyToClipboard(text: string, id: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(id)
      setTimeout(() => setCopied(null), 2000)
    })
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-14">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1 rounded-full mb-3">
            <span>⚠</span> DEMO ONLY — Development Mode
          </div>
          <h1 className="font-display text-2xl font-bold text-ink-900 flex items-center gap-3">
            <MessageSquare className="w-7 h-7 text-brand-500" />
            Mock SMS Inbox
          </h1>
          <p className="text-ink-500 mt-2 text-sm max-w-lg">
            In production, these messages would be sent via SMS to the citizen's verified phone number.
            In demo mode, they are captured here so you can complete the workflow without a real SMS provider.
          </p>
        </div>
        <button
          onClick={loadMessages}
          className="shrink-0 flex items-center gap-2 text-sm text-ink-500 hover:text-brand-500 transition-colors px-3 py-2 rounded-lg border border-ink-100 hover:border-brand-200"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Auto-refresh indicator */}
      <div className="flex items-center gap-2 text-xs text-ink-400 mb-6">
        <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
        Auto-refreshing every 3 seconds
      </div>

      {loading ? (
        <div className="text-center py-16 text-ink-400">Loading messages…</div>
      ) : messages.length === 0 ? (
        <div className="card p-10 text-center text-ink-400">
          <MessageSquare className="w-10 h-10 mx-auto mb-4 opacity-30" />
          <p className="font-medium">No messages yet</p>
          <p className="text-sm mt-1">Messages appear here when a citizen registers or an official creates an instruction.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {messages.map((msg) => {
            const token = extractToken(msg.message)
            const otp = extractOTP(msg.message)
            const verifyUrl = token ? `http://localhost:5173/verify?token=${token}` : null

            return (
              <div key={msg.id} className="card p-5">
                {/* Meta row */}
                <div className="flex items-center justify-between gap-4 mb-3">
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-full bg-brand-100 text-brand-600 text-xs font-bold flex items-center justify-center">
                      {msg.id}
                    </span>
                    <div>
                      <p className="font-mono text-sm font-semibold text-ink-900">{msg.phone_number}</p>
                      <p className="text-xs text-ink-400">
                        {new Date(msg.timestamp).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'medium' })}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-ink-100 text-ink-500 font-medium">
                    {msg.status}
                  </span>
                </div>

                {/* Message body */}
                <pre className="text-sm text-ink-700 bg-ink-50 rounded-lg p-4 whitespace-pre-wrap font-mono leading-relaxed">
                  {msg.message}
                </pre>

                {/* Quick action buttons */}
                <div className="flex flex-wrap gap-2 mt-3">
                  {otp && (
                    <button
                      onClick={() => copyToClipboard(otp, `otp-${msg.id}`)}
                      className="inline-flex items-center gap-1.5 text-xs bg-brand-500 text-white px-3 py-1.5 rounded-lg hover:bg-brand-600 transition-colors font-medium"
                    >
                      {copied === `otp-${msg.id}` ? <CheckCheck className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy OTP: {otp}
                    </button>
                  )}
                  {token && (
                    <button
                      onClick={() => copyToClipboard(token, `token-${msg.id}`)}
                      className="inline-flex items-center gap-1.5 text-xs bg-ink-800 text-white px-3 py-1.5 rounded-lg hover:bg-ink-900 transition-colors font-mono"
                    >
                      {copied === `token-${msg.id}` ? <CheckCheck className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      {token}
                    </button>
                  )}
                  {verifyUrl && (
                    <button
                      onClick={() => navigate(`/verify?token=${token}`)}
                      className="inline-flex items-center gap-1.5 text-xs bg-mint/10 text-mint px-3 py-1.5 rounded-lg hover:bg-mint/20 transition-colors font-medium"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Open verify page
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      <p className="text-center text-xs text-ink-300 mt-10">
        This page is only available in development mode (ENVIRONMENT=development)
      </p>
    </div>
  )
}
