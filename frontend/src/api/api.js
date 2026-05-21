import axios from 'axios'

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

const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = storage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const isAuthEndpoint = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh') || original?.url?.includes('/auth/register')
    if (error.response?.status === 401 && !original._retry && !isAuthEndpoint) {
      original._retry = true
      try {
        const refresh = storage.getItem('refresh_token')
        const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refresh })
        storage.setItem('access_token', data.access_token)
        storage.setItem('refresh_token', data.refresh_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        storage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  changePassword: (data) => api.put('/auth/change-password', data),
  updateProfile: (data) => api.patch('/auth/profile', data),
}

export const topicsApi = {
  list: (params) => api.get('/topics', { params }),
  get: (id) => api.get(`/topics/${id}`),
  create: (data) => api.post('/topics', data),
  update: (id, data) => api.patch(`/topics/${id}`, data),
  delete: (id) => api.delete(`/topics/${id}`),
  submit: (id) => api.post(`/topics/${id}/submit`),
  approve: (id, data = null) => api.post(`/topics/${id}/approve`, data),
  reject: (id, data) => api.post(`/topics/${id}/reject`, data),
  assignSupervisor: (id, data) => api.post(`/topics/${id}/assign-supervisor`, data),
  getCatalog: (params) => api.get('/topics/catalog', { params }),
  createCatalog: (data) => api.post('/topics/catalog', data),
  selectCatalog: (id) => api.post(`/topics/catalog/${id}/select`),
  autoAssign: (academic_year) => api.post('/topics/auto-assign', null, { params: { academic_year } }),
  propose: (data) => api.post('/topics/propose', data),
}

export const stagesApi = {
  list: (topicId) => api.get(`/topics/${topicId}/stages`),
  create: (topicId, data) => api.post(`/topics/${topicId}/stages`, data),
  update: (topicId, stageId, data) => api.patch(`/topics/${topicId}/stages/${stageId}`, data),
  submit: (topicId, stageId) => api.post(`/topics/${topicId}/stages/${stageId}/submit`),
  review: (topicId, stageId, data) => api.post(`/topics/${topicId}/stages/${stageId}/review`, data),
  delete: (topicId, stageId) => api.delete(`/topics/${topicId}/stages/${stageId}`),
  start: (topicId, stageId) => api.post(`/topics/${topicId}/stages/${stageId}/start`),
}

export const filesApi = {
  list: (topicId, stageId) => api.get(`/topics/${topicId}/files${stageId ? `?stage_id=${stageId}` : ''}`),
  upload: (topicId, formData, stageId) =>
    api.post(`/topics/${topicId}/files${stageId ? `?stage_id=${stageId}` : ''}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  delete: (topicId, fileId) => api.delete(`/topics/${topicId}/files/${fileId}`),
  addComment: (topicId, fileId, data) => api.post(`/topics/${topicId}/files/${fileId}/comments`, data),
  downloadUrl: (topicId, fileId) => `/api/v1/topics/${topicId}/files/${fileId}/download`,
  download: async (topicId, fileId, fileName) => {
    const { data } = await api.get(`/topics/${topicId}/files/${fileId}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },
}

export const tasksApi = {
  list: (topicId) => api.get(`/topics/${topicId}/tasks`),
  create: (topicId, data) => api.post(`/topics/${topicId}/tasks`, data),
  update: (topicId, taskId, data) => api.patch(`/topics/${topicId}/tasks/${taskId}`, data),
  delete: (topicId, taskId) => api.delete(`/topics/${topicId}/tasks/${taskId}`),
}

export const meetingsApi = {
  listAll: () => api.get('/meetings'),
  list: (topicId) => api.get(`/meetings/topic/${topicId}`),
  myStudents: () => api.get('/users/supervisor/my-students'),
  create: (data) => api.post('/meetings', data),
  update: (id, data) => api.patch(`/meetings/${id}`, data),
  delete: (id) => api.delete(`/meetings/${id}`),
}

export const notificationsApi = {
  list: () => api.get('/notifications'),
  markRead: (id) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
}

export const messagesContactsApi = {
  contacts: () => api.get('/messages/contacts'),
  conversation: (userId) => api.get(`/messages/conversation/${userId}`),
  send: (data) => api.post('/messages', data),
  groupMessages: (topicId) => api.get(`/messages/group/${topicId}`),
  sendGroup: (data) => api.post('/messages/group', data),
  supervisorGroup: (supervisorUserId) => api.get(`/messages/supervisor-group/${supervisorUserId}`),
  sendSupervisorGroup: (data) => api.post('/messages/supervisor-group', data),
}

export const analysisApi = {
  analyzeText: (data) => api.post('/analysis/text', data),
  getTextQuality: (topicId) => api.get(`/analysis/topic/${topicId}`),
}

export const riskApi = {
  assess: (topicId) => api.post(`/risk/assess/${topicId}`),
  list: () => api.get('/risk/assessments'),
  get: (topicId) => api.get(`/risk/assessment/${topicId}`),
}

export const reportsApi = {
  dashboard: () => api.get('/reports/dashboard'),
  analytics: () => api.get('/reports/analytics'),
}

export const usersApi = {
  list: (role) => api.get('/users', { params: role ? { role } : {} }),
  supervisors: () => api.get('/users/supervisors'),
  supervisorStudents: () => api.get('/users/supervisor/my-students'),
  search: (q) => api.get('/users/search', { params: { q } }),
  mySupervisor: () => api.get('/users/my-supervisor'),
  create: (data) => api.post('/users', data),
  deactivate: (id) => api.patch(`/users/${id}/deactivate`),
  kafedras: () => api.get('/users/admin/kafedras'),
  groups: () => api.get('/users/admin/groups'),
}

export default api
