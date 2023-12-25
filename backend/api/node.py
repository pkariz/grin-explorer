from django.conf import settings

import json
import logging
import requests


logger = logging.getLogger(__name__)


class NodeError(Exception):
    def __init__(self, method, params, code, reason):
        self.method = method
        self.params = params
        self.code = code    # may be None, not all errors have a code
        self.reason = reason
        super().__init__(self.reason)

    def __str__(self):
        return (
            f'Calling node foreign api {self.method} with params {self.params} '
            f'failed with error code {self.code} because: {self.reason}'
        )


class NodeBlockNotFoundException(Exception):
    pass


class NodeBlocksFetchException(Exception):
    pass


class NodeUnknownException(Exception):
    pass


class NodeV2API:
    def __init__(self, node):
        self.foreign_api_url = node.api_url
        self.foreign_api_user = node.api_username
        self.foreign_api_password = node.api_password
        self._cached_blocks = {}
        

    def post(self, method, params):
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params
        }

        response = requests.post(
            self.foreign_api_url,
            json=payload, 
            auth=(self.foreign_api_user, self.foreign_api_password),
            # long read timeout because of node's compaction process
            timeout=(5, 60)
        )

        if response.status_code >= 300 or response.status_code < 200:
            # Requests-level error
            raise NodeError(
                method, params, response.status_code, response.reason)
        response_json = response.json()

        # https://github.com/mimblewimble/grin-rfcs/blob/master/text/0007-node-api-v2.md#errors
        if "error" in response_json:
            # One version of a node error
            raise NodeError(
                method, params,
                response_json["error"]["code"],
                response_json["error"]["message"]
            )
        if "Err" in response_json:
            # Another version of a node error
            raise NodeError(
                method, params, None, response_json["result"]["Err"])
        return response_json

    def get_tip(self):
        resp = self.post('get_tip', [])
        return resp["result"]["Ok"]
    
    def get_kernel(self, excess, min_height=None, max_height=None):
        resp = self.post('get_kernel', [excess, min_height, max_height])
        return resp["result"]["Ok"]

    def get_header(self, height=None, hash=None, commit=None):
        resp = self.post('get_header', [height, hash, commit])
        return resp["result"]["Ok"]

    def get_block(self, height=None, hash=None, commit=None):
        resp = self.post('get_block', [height, hash, commit])
        res = resp['result']
        try:
            return resp["result"]["Ok"]
        except KeyError:
            if 'Err' in resp['result'] and resp['result']['Err'] == 'NotFound':
                logger.warning(
                    'NodeBlockNotFoundException',
                    extra={ 'height': height, 'hash': hash },
                )
                raise NodeBlockNotFoundException()
            log_data = json.dumps(resp)
            logger.error('NodeUnknownException', extra={ 'result': log_data })
            raise NodeUnknownException()

    def get_blocks(self, start_height, end_height, limit=1000, proofs=True):
        if start_height < 0:
            raise Exception('Starting height must >= 0.')
        if not 1 <= limit <= 1000:
            raise Exception('Limit must be between 1 and 1000.')
        resp = self.post('get_blocks', [start_height, end_height, limit, proofs])
        res = resp['result']
        try:
            return resp["result"]["Ok"]
        except KeyError:
            if 'Err' in resp['result'] and resp['result']['Err'] == 'NotFound':
                logger.warning(
                    'NodeBlocksFetchException',
                    extra={ 'start_height': start_height, 'end_height': end_height },
                )
                raise NodeBlocksFetchException()
            log_data = json.dumps(resp)
            logger.error('NodeUnknownException', extra={ 'result': log_data })
            raise NodeUnknownException()

