import { api } from '@/services/auth'

export default {
  addBlockchain(data) {
    return api.post(`/blockchains/`, data)
  },
  fetchBlockchains() {
    return api.get(`/blockchains/`)
      .then(response => {
        return response.data;
      })
  },
  editBlockchain(slug, data) {
    return api.patch(`/blockchains/${slug}/`, data)
  },
  deleteBlockchain(slug) {
    return api.delete(`/blockchains/${slug}/`)
  },
  bootstrapBlockchain(slug) {
    return api.post(`/blockchains/${slug}/bootstrap/`, {})
  },
  abortBootstrap(slug) {
    return api.post(`/blockchains/${slug}/bootstrap/abort/`, {})
  },
  fetchGraphs(slug) {
    return api.get(`/blockchains/${slug}/graphs/`)
      .then(response => {
        return response.data;
      })
  },
}
