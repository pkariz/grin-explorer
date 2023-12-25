import { api } from '@/services/auth'

export default {
  fetchBlocks(blockchain, page, pageSize) {
    return api.get(`/blockchains/${blockchain}/blocks/?page=${page}&page_size=${pageSize}`)
      .then(response => response.data)
  },
  fetchBlock(blockchain, blockHash) {
    return api.get(`/blockchains/${blockchain}/blocks/${blockHash}/`)
      .then(response => response.data)
  },
  searchBlocks(blockchain, search, page, pageSize) {
    return api.get(`/blockchains/${blockchain}/blocks/?search=${search}&page=${page}&page_size=${pageSize}`)
      .then(response => response.data)
  },
}
