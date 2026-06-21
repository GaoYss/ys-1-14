import { http } from './http'

export const recordsApi = {
  list(params = {}) {
    return http.get('/records', { params })
  },
  options() {
    return http.get('/records/options')
  },
  create(payload) {
    return http.post('/records', payload)
  }
}
