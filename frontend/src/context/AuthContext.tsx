import { createContext, useContext, useState, ReactNode, useEffect } from 'react'
import { api, type AuthUser, getToken, clearToken } from '@/services/api'

interface AuthContextType {
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (phone: string, password: string) => Promise<void>
  registerCitizen: (name: string, phone: string, password: string, aadhaar: string) => Promise<void>
  registerOfficial: (name: string, phone: string, password: string, institutionId: string, officialId: string) => Promise<void>
  sendOTP: (phone: string) => Promise<void>
  verifyOTP: (phone: string, otp: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Restore session if a token is already stored (page refresh / returning user)
    const initAuth = async () => {
      try {
        if (getToken()) {
          const currentUser = await api.getCurrentUser()
          setUser(currentUser)
        }
      } catch {
        clearToken()
      } finally {
        setIsLoading(false)
      }
    }
    initAuth()
  }, [])

  const login = async (phone: string, password: string) => {
    setIsLoading(true)
    try {
      // api.login() stores the JWT in localStorage and sets the axios header
      await api.login(phone, password)
      // Fetch the authoritative user record (real name + role from JWT) from backend
      const currentUser = await api.getCurrentUser()
      setUser(currentUser)
    } finally {
      setIsLoading(false)
    }
  }

  const registerCitizen = async (name: string, phone: string, password: string, aadhaar: string) => {
    setIsLoading(true)
    try {
      await api.registerCitizen(name, phone, password, aadhaar)
      // After registration, user needs to verify OTP before they can login
    } finally {
      setIsLoading(false)
    }
  }

  const registerOfficial = async (name: string, phone: string, password: string, institutionId: string, officialId: string) => {
    setIsLoading(true)
    try {
      await api.registerOfficial(name, phone, password, institutionId, officialId)
      // After registration, official can login directly
    } finally {
      setIsLoading(false)
    }
  }

  const sendOTP = async (phone: string) => {
    await api.sendOTP(phone)
  }

  const verifyOTP = async (phone: string, otp: string) => {
    setIsLoading(true)
    try {
      // api.verifyOTP() stores the access token returned after OTP verification
      await api.verifyOTP(phone, otp)
      // Fetch full user details from backend (authoritative name + role)
      const currentUser = await api.getCurrentUser()
      setUser(currentUser)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    clearToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        registerCitizen,
        registerOfficial,
        sendOTP,
        verifyOTP,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
