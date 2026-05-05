import { create } from 'zustand'
import { authApi } from '../api/api'

const useAuthStore = create((set, get) => ({
  user: null,
  loading: true,

  init: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) return set({ loading: false })
    try {
      const { data } = await authApi.me()
      set({ user: data, loading: false })
    } catch {
      localStorage.clear()
      set({ loading: false })
    }
  },

  login: async (credentials) => {
    const { data } = await authApi.login(credentials)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    set({ user: data.user })
    return data
  },

  logout: () => {
    localStorage.clear()
    set({ user: null })
  },

  isRole: (...roles) => roles.includes(get().user?.role),
}))

export default useAuthStore
