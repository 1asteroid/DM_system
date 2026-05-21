import { create } from 'zustand'
import { authApi } from '../api/api'

const storage = {
  getItem: (key) => {
    try {
      return localStorage.getItem(key)
    } catch {
      return sessionStorage.getItem(key)
    }
  },
  setItem: (key, value) => {
    try {
      localStorage.setItem(key, value)
    } catch {
      sessionStorage.setItem(key, value)
    }
  },
  removeItem: (key) => {
    try {
      localStorage.removeItem(key)
    } catch {}
    try {
      sessionStorage.removeItem(key)
    } catch {}
  },
  clear: () => {
    try {
      localStorage.clear()
    } catch {}
    try {
      sessionStorage.clear()
    } catch {}
  }
}

const useAuthStore = create((set, get) => ({
  user: null,
  loading: true,

  init: async () => {
    const token = storage.getItem('access_token')
    if (!token) return set({ loading: false })
    try {
      const { data } = await authApi.me()
      set({ user: data, loading: false })
    } catch {
      storage.clear()
      set({ loading: false })
    }
  },

  login: async (credentials) => {
    const { data } = await authApi.login(credentials)
    storage.setItem('access_token', data.access_token)
    storage.setItem('refresh_token', data.refresh_token)
    set({ user: data.user })
    return data
  },

  logout: () => {
    storage.clear()
    set({ user: null })
  },

  isRole: (...roles) => roles.includes(get().user?.role),
}))

export default useAuthStore
