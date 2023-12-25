import { api } from '@/services/auth'

export default {
  addNodeGroup(data) {
    return api.post(`/node-groups/`, data)
  },
  fetchNodeGroups() {
    return api.get(`/node-groups/`)
      .then(response => {
        return response.data;
      })
  },
  editNodeGroup(slug, data) {
    return api.patch(`/node-groups/${slug}/`, data)
  },
  deleteNodeGroup(slug) {
    return api.delete(`/node-groups/${slug}/`)
  },
}
