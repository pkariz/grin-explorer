import { api } from '@/services/auth'

export default {
  addNode(data) {
    return api.post(`/nodes/`, data)
  },
  fetchNodes() {
    return api.get(`/nodes/`)
      .then(response => {
        return response.data;
      })
  },
  editNode(slug, data) {
    return api.patch(`/nodes/${slug}/`, data)
  },
  deleteNode(slug) {
    return api.delete(`/nodes/${slug}/`)
  },
  fetchReachable(slug) {
    // timeout is higher because it takes time to check whether the node is reachable
    return api.get(`/nodes/${slug}/reachable/`, { timeout: 30000 })
      .then(response => {
        return response.data;
      })
  },
}
