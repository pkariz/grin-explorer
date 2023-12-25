from django.test import TestCase
from .models import (
    Blockchain,
    Block,
    BlockHeader,
    Input,
    Output,
    Kernel,
    Reorg,
    Node,
    NodeGroup,
)
from .bootstrap import fetch_and_store_block
from unittest.mock import patch, Mock

import json


class ReorgTestCase(TestCase):
    def setUp(self):
        self.patcher = patch('backend.api.bootstrap.NodeV2API')
        self.nodeV2APIMock = self.patcher.start()
        node_group = NodeGroup.objects.create(name='foo group')
        node = Node.objects.create(
            name='test',
            api_url='foo_url',
            api_username='foouser',
            api_password='foopw',
            archive=False,
            group=node_group,
        )
        self.blockchain = Blockchain.objects.create(
            name='test',
            node=node,
            default=True,
            fetch_price=False,
        )

    def tearDown(self):
        self.patcher.stop()

    def to_hex(self, s):
        # in some cases some previous hash might be None
        if s is None:
            return
        return bytes(s, 'utf-8').hex()

    def _get_fake_header(self, height, hash, prev_hash):
        return {
            'cuckoo_solution': list(range(1, 43)),
            'edge_bits': 32,
            'hash': self.to_hex(hash),
            'height': height,
            'kernel_mmr_size': 1,
            'kernel_root': 'foo-kernel-root',
            'nonce': 1,
            'output_mmr_size': 1,
            'output_root': 'foo-output-root',
            'prev_root': 'foo-prev-root',
            'previous': self.to_hex(prev_hash),
            'range_proof_root': 'foo-range-proof-root',
            'secondary_scaling': 0,
            'timestamp': '2000-01-01T00:00:00+00:00',
            'total_difficulty': 1,
            'total_kernel_offset': 'foo-total-kernel-offset',
            'version': 5,
        }

    def _get_fake_block(self, height, prev_hash, inputs, outputs):
        return {
            'header': {
                'previous': self.to_hex(prev_hash),
            },
            'inputs': inputs,
            'kernels': [
                {
                    'excess': 'foo-excess',
                    'excess_sig': 'foo-excess-sig',
                    'features': 'Plain',
                    'fee': 30000000,
                    'fee_shift': 0,
                    'lock_height': 0,
                },
            ],
            'outputs': outputs,
        }

    def _get_accepted_block_data(self, height, hash, prev_hash):
        # return only the data that's read in the view
        if prev_hash:
            # we convert prev_hash to bytearray (but as list of ints) because
            # that's what's POST-ed to the accepted-block API.
            prev_hash = [x for x in bytearray(bytes.fromhex(prev_hash))]
        return {
            'data': {
                'body': {},
                'header': {
                    'height': height,
                    'prev_hash': prev_hash,
                },
            },
            # here hash is already hex
            'hash': hash,
        }

    def _get_output(self, height, commit, spent):
        return {
            'block_height': height,
            'commit': commit,
            'merkle_proof': None,
            'mmr_index': 0,
            'output_type': 'Transaction',
            'proof': 'foo-proof',
            'proof_hash': 'foo-proof-hash',
            'spent': spent,
        }


    def test_reorg_through_accepted_block_view(self):
        """
        Test nested reorg scenario for accepted-block view.

        0 = main chain
        1 and 2 = Reorg 1 and Reorg 2

        BLOCK ORDER:
          100 --> 100(0)
          101.2 --> 100(0), 101.2(0)
          102.3 --> 100(0), 101.2(0), 102.3(0)
          103.3 --> 100(0), 101.2(0), 102.3(0), 103.3(0)
          102.2 --> 100(0), 101.2(0), 102.2(0):
                        FIND AND MARK OLD AS REORG 1: 102.3(1), 103.3(1)
          103.2 --> 100(0), 101.2(0), 102.2(0), 103.2(0):
                        THE OLD ONES STAY THE SAME: 102.3(1), 103.3(1)
          104.2 --> 100(0), 101.2(0), 102.2(0), 103.2(0), 104.2(0):
                        THE OLD ONES STAY THE SAME: 102.3(1), 103.3(1)
          105.2 --> 100(0), 101.2(0), 102.2(0), 103.2(0), 104.2(0), 105.2(0):
                        THE OLD ONES STAY THE SAME: 102.3(1), 103.3(1)
          101 --> 100(0), 101(0):
                        FIND AND MARK OLD AS REORG 2: 101.2(2), 102.2(2), 103.2(2), 104.2(2), 105.2(2)
                        PREVIOUS REORGS: 102.3(1), 103.3(1)
          102 --> 100(0), 101(0), 102(0):
                        THE OLD ONES STAY THE SAME: 102.3(1), 103.3(1), 101.2(2), 102.2(2), 103.2(2), 104.2(2), 105.2(2)
          103 --> 100(0), 101(0), 102(0), 103(0):
                        THE OLD ONES STAY THE SAME: 102.3(1), 103.3(1), 101.2(2), 102.2(2), 103.2(2), 104.2(2), 105.2(2)
        """
        from backend.api.bootstrap import NodeV2API

        # define header/block sequence as defined in the function docstring
        headers = [
            self._get_fake_header(1, 'h100', None),  # genesis
            self._get_fake_header(2, 'h101.2', 'h100'),
            self._get_fake_header(3, 'h102.3', 'h101.2'),
            self._get_fake_header(4, 'h103.3', 'h102.3'),
            self._get_fake_header(3, 'h102.2', 'h101.2'),  # first reorg
            self._get_fake_header(4, 'h103.2', 'h102.2'),
            self._get_fake_header(5, 'h104.2', 'h103.2'),
            self._get_fake_header(6, 'h105.2', 'h104.2'),
            self._get_fake_header(2, 'h101', 'h100'),  # second reorg
            self._get_fake_header(3, 'h102', 'h101'),
            self._get_fake_header(4, 'h103', 'h102'),
        ]
        blocks = [
            self._get_fake_block(1, None, [], [
                self._get_output(1, 'g1', False),
                self._get_output(1, 'g2', False),
                self._get_output(1, 'g3', False)
            ]),  # genesis - h100
            self._get_fake_block(2, 'h100', ['g1'], [
                self._get_output(2, 'a', False),
            ]),  # h101.2
            self._get_fake_block(3, 'h101.2', ['g2', 'a'], [
                self._get_output(3, 'f', False),
                self._get_output(3, 'b', False),
                self._get_output(3, 'c', False),
            ]),  # h102.3
            self._get_fake_block(4, 'h102.3', ['c'], [
                self._get_output(4, 'h', False)
            ]),  # h103.3
            self._get_fake_block(3, 'h101.2', ['a'], [
                self._get_output(3, 'b', False),
                self._get_output(3, 'c', False),
            ]),  # first reorg - h102.2
            self._get_fake_block(4, 'h102.2', ['b'], [
                self._get_output(4, 'd', False),
            ]),  # 103.2
            self._get_fake_block(5, 'h103.2', [], []),  # 104.2
            self._get_fake_block(6, 'h104.2', ['c'], [
                self._get_output(6, 'e', False),
            ]),  # 105.2
            self._get_fake_block(2, 'h100', ['g1'], [
                self._get_output(2, 'a', False),
            ]),  # second reorg - h101
            self._get_fake_block(3, 'h101', ['g3', 'a'], [
                self._get_output(3, 'i', False),
                self._get_output(3, 'b', False),
                self._get_output(3, 'c', False),
            ]),  # h102
            self._get_fake_block(4, 'h102', ['b'], [
                self._get_output(4, 'd', False),
            ]),  # h103
        ]
        # make sure node returns reorg data as defined in the function docs
        node_instance_mock = Mock()
        node_instance_mock.get_header.side_effect = headers
        node_instance_mock.get_block.side_effect = blocks
        self.nodeV2APIMock.return_value = node_instance_mock
        # send new blocks to accepted-block view (includes 2 reorgs)
        for i in range(0, len(headers)):
            header = headers[i]
            post_data = self._get_accepted_block_data(
                header['height'], header['hash'], header['previous']
            )
            self.client.post(
                f'/api/blockchains/{self.blockchain.slug}/accepted/',
                json.dumps(post_data),
                content_type="application/json"
            )
        # validate correctness of the main chain block sequence
        main_chain_blocks = self.blockchain.blocks\
            .filter(reorg__isnull=True)\
            .order_by('height')
        expected_main_chain = [
            { 'height': 1, 'hash': self.to_hex('h100'), 'prev_hash': None },
            { 'height': 2, 'hash': self.to_hex('h101'), 'prev_hash': self.to_hex('h100') },
            { 'height': 3, 'hash': self.to_hex('h102'), 'prev_hash': self.to_hex('h101') },
            { 'height': 4, 'hash': self.to_hex('h103'), 'prev_hash': self.to_hex('h102') },
        ]
        actual_main_chain = [
            {
                'height': block.height,
                'hash': block.hash,
                'prev_hash': block.prev_hash,
            }
            for block in main_chain_blocks
        ]
        self.assertEqual(actual_main_chain, expected_main_chain)
        # reorgs validation
        self.assertEqual(Reorg.objects.count(), 2)
        # validate correctness of the first reorg
        reorg1 = Reorg.objects.first()
        self.assertEqual(reorg1.blockchain, self.blockchain)
        self.assertEqual(reorg1.start_reorg_block.hash, self.to_hex('h102.3'))
        self.assertEqual(reorg1.end_reorg_block.hash, self.to_hex('h103.3'))
        self.assertEqual(reorg1.start_main_block.hash, self.to_hex('h102.2'))
        # validate correctness of the second reorg
        reorg2 = Reorg.objects.last()
        self.assertEqual(reorg2.blockchain, self.blockchain)
        self.assertEqual(reorg2.start_reorg_block.hash, self.to_hex('h101.2'))
        self.assertEqual(reorg2.end_reorg_block.hash, self.to_hex('h105.2'))
        self.assertEqual(reorg2.start_main_block.hash, self.to_hex('h101'))
        # validate all inputs
        main_inputs = set(map(
            lambda input: (
                input.commitment,
                input.output.block.hash if input.output else None,
                input.block.reorg.id if input.block.reorg else None
            ),
            Input.objects.all()
        ))
        expected_inputs = set([
            # pairs (<commitment>, <block_hash_of_related_output>, <reorgID>)
            # main
            ('g1', self.to_hex('h100'), None),
            ('g3', self.to_hex('h100'), None),
            ('a', self.to_hex('h101'), None),
            ('b', self.to_hex('h102'), None),
            # reorg 2
            ('g1', self.to_hex('h100'), 2),
            ('a', self.to_hex('h101.2'), 2),
            ('b', self.to_hex('h102.2'), 2),
            ('c', self.to_hex('h102.2'), 2),
            # reorg 1
            ('g2', self.to_hex('h100'), 1),
            ('a', self.to_hex('h101.2'), 1),
            ('c', self.to_hex('h102.3'), 1),
        ])
        self.assertEqual(main_inputs, expected_inputs)
        # validate all outputs
        main_outputs = set(map(
            lambda output: (
                output.commitment,
                output.block.hash,
                output.spent,
                tuple(sorted(map(
                    lambda input: input.block.hash,
                    output.inputs.all()
                )))
            ),
            Output.objects.all()
        ))
        expected_outputs = set([
            # (<commitment>, <output_block_hash>, <spent>, <set_of_inputs<(block_hash)>>)
            # main outputs
            ('g1', self.to_hex('h100'), True, (self.to_hex('h101'), self.to_hex('h101.2'))),
            ('g2', self.to_hex('h100'), False, (self.to_hex('h102.3'),)),
            ('g3', self.to_hex('h100'), True, (self.to_hex('h102'),)),
            ('a', self.to_hex('h101'), True, (self.to_hex('h102'),)),
            ('i', self.to_hex('h102'), False, tuple()),
            ('b', self.to_hex('h102'), True, (self.to_hex('h103'),)),
            ('c', self.to_hex('h102'), False, tuple()),
            ('d', self.to_hex('h103'), False, tuple()),
            # reorg 2 outputs
            ('a', self.to_hex('h101.2'), True, (self.to_hex('h102.2'), self.to_hex('h102.3'))),
            ('b', self.to_hex('h102.2'), True, (self.to_hex('h103.2'),)),
            ('c', self.to_hex('h102.2'), True, (self.to_hex('h105.2'),)),
            ('d', self.to_hex('h103.2'), False, tuple()),
            ('e', self.to_hex('h105.2'), False, tuple()),
            # reorg 1 outputs
            ('f', self.to_hex('h102.3'), False, tuple()),
            ('b', self.to_hex('h102.3'), False, tuple()),
            ('c', self.to_hex('h102.3'), True, (self.to_hex('h103.3'),)),
            ('h', self.to_hex('h103.3'), False, tuple()),
        ])
        self.assertEqual(main_outputs, expected_outputs)

    def test_reorg_through_load_blocks(self):
        """
        Test reorg scenario for load_blocks (used when bootstraping).

        0 = main chain
        1 = Reorg 1

        BLOCK ORDER:
          100 --> 100(0)
          101 --> 100(0), 101(0)
          102.1 --> 100(0), 101(0), 102.1(0)
          103.1 --> 100(0), 101(0), 102.1(0), 103.1(0)
          102 --> 100(0), 101(0), 102(0):
                        FIND AND MARK OLD AS REORG 1: 102.1(1), 103.1(1)
          103 --> 100(0), 101(0), 102(0), 103(0):
                        THE OLD ONES STAY THE SAME: 102.1(1), 103.1(1)
          104 --> 100(0), 101(0), 102(0), 103(0), 104(0):
                        THE OLD ONES STAY THE SAME: 102.1(1), 103.1(1)
          105 --> 100(0), 101(0), 102(0), 103(0), 104(0), 105(0):
                        THE OLD ONES STAY THE SAME: 102.1(1), 103.1(1)
        """
        from backend.api.bootstrap import NodeV2API, load_blocks

        headers = [
            self._get_fake_header(4, 'h103.1', 'h102.1'),
            self._get_fake_header(3, 'h102.1', 'h101'),
            self._get_fake_header(2, 'h101', 'h100'),
            self._get_fake_header(1, 'h100', None),  # genesis
            # second load_blocks call
            self._get_fake_header(6, 'h105', 'h104'),
            self._get_fake_header(5, 'h104', 'h103'),
            self._get_fake_header(4, 'h103', 'h102'),
            self._get_fake_header(3, 'h102', 'h101'),  # reorg
        ]
        blocks = [
            self._get_fake_block(
                4, 'h102.1', ['b'], [self._get_output(4, 'd', False)]),
            self._get_fake_block(
                3,
                'h101',
                ['a'],
                [
                    self._get_output(3, 'b', True),
                    self._get_output(3, 'c', False),
                ]
            ),
            self._get_fake_block(
                2, 'h100', ['g'], [self._get_output(2, 'a', True)]),
            self._get_fake_block(
                1, None, [], [self._get_output(1, 'g', True)]),  # genesis
            # second load_blocks call
            self._get_fake_block(
                6, 'h104', ['d'], [self._get_output(6, 'f', False)]),
            self._get_fake_block(
                5, 'h103', [], [self._get_output(5, 'e', False)]),
            # 'd' is spent in the new main chain, 'a' is not spent!
            self._get_fake_block(
                4, 'h102', [], [self._get_output('4', 'd', True)]),
            # reorg start, 'b' is not spent in the new main chain
            self._get_fake_block(
                3, 'h101', [], [self._get_output(3, 'b', False)]),
        ]
        # make sure node returns reorg data as defined in the function docs
        node_instance_mock = Mock()
        node_instance_mock.get_header.side_effect = headers
        node_instance_mock.get_block.side_effect = blocks
        self.nodeV2APIMock.return_value = node_instance_mock
        # load initial regular chain
        load_blocks(self.blockchain, 1, 4, True)
        # check if 'spent' is correctly set
        self.assertEqual(
            set(Output.objects\
                .filter(spent=True, block__reorg__isnull=True)\
                .values_list('commitment', flat=True)
            ),
            set(['a', 'b', 'g'])
        )
        # now load reorg
        load_blocks(self.blockchain, 1, 6, False)
        # check if 'spent' is correctly set on the main chain
        self.assertEqual(
            set(Output.objects\
                .filter(spent=True, block__reorg__isnull=True)\
                .values_list('commitment', flat=True)
            ),
            set(['g', 'd'])
        )
        # check that 'b' is marked as spent on the reorged chain and that 'b'
        # input has reference to the correct 'b' output (the reorged Output)
        self.assertEqual(
            set(Output.objects\
                .filter(spent=True, block__reorg__isnull=False)\
                .values_list('commitment', flat=True)
            ),
            set(['b'])
        )
        b_input_reorged = Input.objects.get(
            commitment='b', block__reorg__isnull=False)
        b_output_reorged = Output.objects.get(
            commitment='b', block__reorg__isnull=False)
        self.assertEqual(b_input_reorged.output, b_output_reorged)
        # check that 'b' output on the main chain is marked as unspent and has
        # no related inputs
        b_output_main = Output.objects.get(commitment='b', block__reorg=None)
        self.assertEqual(b_output_main.spent, False)
        self.assertEqual(b_output_main.inputs.count(), 0)
        # check that 'a' input on the reoged chain has reference to the main
        # chain 'a' output
        a_input_reorged = Input.objects.get(
            commitment='a', block__reorg__isnull=False)
        a_output_main = Output.objects.get(commitment='a', block__reorg=None)
        self.assertEqual(a_input_reorged.output, a_output_main)
        # check that output 'd' on the reorged chain is unspent and has no
        # related inputs
        d_output_reorged = Output.objects.get(
            commitment='d', block__reorg__isnull=False)
        self.assertEqual(d_output_reorged.spent, False)
        self.assertEqual(d_output_reorged.inputs.count(), 0)
        # check that output 'd' on the main chain has Input from the main chain
        # related to it and not the Input which is part of the reorg
        d_output_main = Output.objects.get(commitment='d', block__reorg=None)
        d_input_main = Input.objects.get(commitment='d', block__reorg=None)
        self.assertEqual(d_output_main.inputs.count(), 1)
        self.assertEqual(d_output_main.inputs.first(), d_input_main)
        # validate correctness of the main chain state
        main_chain_blocks = self.blockchain.blocks\
            .filter(reorg__isnull=True)\
            .order_by('height')
        expected_main_chain = [
            { 'height': 1, 'hash': self.to_hex('h100'), 'prev_hash': None },
            { 'height': 2, 'hash': self.to_hex('h101'), 'prev_hash': self.to_hex('h100') },
            { 'height': 3, 'hash': self.to_hex('h102'), 'prev_hash': self.to_hex('h101') },
            { 'height': 4, 'hash': self.to_hex('h103'), 'prev_hash': self.to_hex('h102') },
            { 'height': 5, 'hash': self.to_hex('h104'), 'prev_hash': self.to_hex('h103') },
            { 'height': 6, 'hash': self.to_hex('h105'), 'prev_hash': self.to_hex('h104') },
        ]
        actual_main_chain = [
            {
                'height': block.height,
                'hash': block.hash,
                'prev_hash': block.prev_hash,
            }
            for block in main_chain_blocks
        ]
        self.assertEqual(actual_main_chain, expected_main_chain)
        self.assertEqual(Reorg.objects.count(), 1)
        # validate correctness of the reorg
        reorg = Reorg.objects.first()
        self.assertEqual(reorg.blockchain, self.blockchain)
        self.assertEqual(reorg.start_reorg_block.hash, self.to_hex('h102.1'))
        self.assertEqual(reorg.end_reorg_block.hash, self.to_hex('h103.1'))
        self.assertEqual(reorg.start_main_block.hash, self.to_hex('h102'))

    def test_reorg_which_continues_existing_reorg_through_accepted_block_view(self):
        """
        Test nested reorg scenario for accepted-block view.

        0 = main chain
        1 and 2 = Reorg 1 and Reorg 2, where Reorg 1 later becomes part of the
        main chain

        BLOCK ORDER:
          100 --> 100(0)
          101 --> 100(0), 101(0)
          101.1 --> 100(0), 101.1(0): REORGED: 101(1)
          102.1 --> 100(0), 101.1(0), 102.1(0): REORGED: 101(1)
          102 --> 100(0), 101(0), 102(0):  REORGED: 101.1(2), 102.1(2)
        """
        from backend.api.bootstrap import NodeV2API

        # define header/block sequence as defined in the function docstring
        headers = [
            self._get_fake_header(1, 'h100', None),  # genesis
            self._get_fake_header(2, 'h101', 'h100'),
            self._get_fake_header(2, 'h101.1', 'h100'),  # first reorg
            self._get_fake_header(3, 'h102.1', 'h101.1'),
            self._get_fake_header(3, 'h102', 'h101'),  # second reorg
        ]
        blocks = [
            self._get_fake_block(1, None, [], [
                self._get_output(1, 'g1', False),
                self._get_output(1, 'g2', False),
                self._get_output(1, 'g3', False),
                self._get_output(1, 'g4', False),
            ]),  # genesis - h100
            self._get_fake_block(2, 'h100', ['g1'], [
                self._get_output(2, 'a', False),
                self._get_output(2, 'b', False),
            ]),  # h101
            self._get_fake_block(3, 'h100', ['g2', 'g4'], [
                self._get_output(3, 'd', False),
                self._get_output(3, 'i', False),
            ]),  # h101.1 - first reorg
            self._get_fake_block(4, 'h101.1', ['g1', 'g3', 'd'], [
                self._get_output(4, 'a', False),
                self._get_output(4, 'e', False),
                self._get_output(4, 'f', False),
            ]),  # h102.1
            self._get_fake_block(3, 'h101', ['b', 'g2'], [
                self._get_output(3, 'c', False),
                self._get_output(3, 'd', False),
            ]),  # h102 - second reorg
        ]
        # make sure node returns reorg data as defined in the function docs
        node_instance_mock = Mock()
        node_instance_mock.get_header.side_effect = headers
        node_instance_mock.get_block.side_effect = blocks
        self.nodeV2APIMock.return_value = node_instance_mock

        # send first 4 blocks to accepted-block view (includes 1 reorg)
        for i in range(4):
            header = headers[i]
            post_data = self._get_accepted_block_data(
                header['height'], header['hash'], header['previous']
            )
            self.client.post(
                f'/api/blockchains/{self.blockchain.slug}/accepted/',
                json.dumps(post_data),
                content_type="application/json"
            )
        # validate correctness of the main chain block sequence
        main_chain_blocks = self.blockchain.blocks\
            .filter(reorg__isnull=True)\
            .order_by('height')
        expected_main_chain = [
            { 'height': 1, 'hash': self.to_hex('h100'), 'prev_hash': None },
            { 'height': 2, 'hash': self.to_hex('h101.1'), 'prev_hash': self.to_hex('h100') },
            { 'height': 3, 'hash': self.to_hex('h102.1'), 'prev_hash': self.to_hex('h101.1') },
        ]
        actual_main_chain = [
            {
                'height': block.height,
                'hash': block.hash,
                'prev_hash': block.prev_hash,
            }
            for block in main_chain_blocks
        ]
        self.blockchain.full_print()
        self.assertEqual(actual_main_chain, expected_main_chain)
        # reorgs validation
        self.assertEqual(Reorg.objects.count(), 1)
        # validate correctness of the first reorg
        reorg1 = Reorg.objects.first()
        self.assertEqual(reorg1.blockchain, self.blockchain)
        self.assertEqual(reorg1.start_reorg_block.hash, self.to_hex('h101'))
        self.assertEqual(reorg1.end_reorg_block.hash, self.to_hex('h101'))
        self.assertEqual(reorg1.start_main_block.hash, self.to_hex('h101.1'))
        # validate all inputs
        main_inputs = set(map(
            lambda input: (
                input.commitment,
                input.output.block.hash if input.output else None,
                input.block.reorg.id if input.block.reorg else None
            ),
            Input.objects.all()
        ))
        expected_inputs = set([
            # tuples (<commitment>, <block_hash_of_related_output>, <reorgID>)
            # main
            ('g1', self.to_hex('h100'), None),
            ('g2', self.to_hex('h100'), None),
            ('g3', self.to_hex('h100'), None),
            ('g4', self.to_hex('h100'), None),
            ('d', self.to_hex('h101.1'), None),
            # reorg 1
            ('g1', self.to_hex('h100'), reorg1.pk),
        ])
        self.assertEqual(main_inputs, expected_inputs)
        # validate all outputs
        main_outputs = set(map(
            lambda output: (
                output.commitment,
                output.block.hash,
                output.spent,
                tuple(sorted(map(
                    lambda input: input.block.hash,
                    output.inputs.all()
                )))
            ),
            Output.objects.all()
        ))
        expected_outputs = set([
            # (<commitment>, <output_block_hash>, <spent>, <set_of_inputs<(block_hash)>>)
            # main outputs
            ('g1', self.to_hex('h100'), True, (self.to_hex('h101'), self.to_hex('h102.1'))),
            ('g2', self.to_hex('h100'), True, (self.to_hex('h101.1'),)),
            ('g3', self.to_hex('h100'), True, (self.to_hex('h102.1'),)),
            ('g4', self.to_hex('h100'), True, (self.to_hex('h101.1'),)),

            ('d', self.to_hex('h101.1'), True, (self.to_hex('h102.1'),)),
            ('i', self.to_hex('h101.1'), False, tuple()),
            ('e', self.to_hex('h102.1'), False, tuple()),
            ('a', self.to_hex('h102.1'), False, tuple()),
            ('f', self.to_hex('h102.1'), False, tuple()),
            # reorg 1 outputs
            ('a', self.to_hex('h101'), False, tuple()),
            ('b', self.to_hex('h101'), False, tuple()),
        ])
        self.assertEqual(main_outputs, expected_outputs)
        # send the last block to accepted-block view (creates a new reorg)
        header = headers[-1]
        post_data = self._get_accepted_block_data(
            header['height'], header['hash'], header['previous']
        )
        self.client.post(
            f'/api/blockchains/{self.blockchain.slug}/accepted/',
            json.dumps(post_data),
            content_type="application/json"
        )
        # validate correctness of the main chain block sequence
        main_chain_blocks = self.blockchain.blocks\
            .filter(reorg__isnull=True)\
            .order_by('height')
        expected_main_chain = [
            { 'height': 1, 'hash': self.to_hex('h100'), 'prev_hash': None },
            { 'height': 2, 'hash': self.to_hex('h101'), 'prev_hash': self.to_hex('h100') },
            { 'height': 3, 'hash': self.to_hex('h102'), 'prev_hash': self.to_hex('h101') },
        ]
        actual_main_chain = [
            {
                'height': block.height,
                'hash': block.hash,
                'prev_hash': block.prev_hash,
            }
            for block in main_chain_blocks
        ]
        self.assertEqual(actual_main_chain, expected_main_chain)
        # reorgs validation
        self.assertEqual(Reorg.objects.count(), 1)
        # validate correctness of the second reorg
        reorg1 = Reorg.objects.first()
        self.assertEqual(reorg1.blockchain, self.blockchain)
        self.assertEqual(reorg1.start_reorg_block.hash, self.to_hex('h101.1'))
        self.assertEqual(reorg1.end_reorg_block.hash, self.to_hex('h102.1'))
        self.assertEqual(reorg1.start_main_block.hash, self.to_hex('h101'))
        # validate all inputs
        main_inputs = set(map(
            lambda input: (
                input.commitment,
                input.output.block.hash if input.output else None,
                input.block.reorg.id if input.block.reorg else None
            ),
            Input.objects.all()
        ))
        expected_inputs = set([
            # tuples (<commitment>, <block_hash_of_related_output>, <reorgID>)
            # main
            ('g1', self.to_hex('h100'), None),
            ('b', self.to_hex('h101'), None),
            ('g2', self.to_hex('h100'), None),
            # reorg 2
            ('g2', self.to_hex('h100'), reorg1.pk),
            ('g4', self.to_hex('h100'), reorg1.pk),
            ('g3', self.to_hex('h100'), reorg1.pk),
            ('g1', self.to_hex('h100'), reorg1.pk),
            ('d', self.to_hex('h101.1'), reorg1.pk),
        ])
        self.assertEqual(main_inputs, expected_inputs)
        # validate all outputs
        main_outputs = set(map(
            lambda output: (
                output.commitment,
                output.block.hash,
                output.spent,
                tuple(sorted(map(
                    lambda input: input.block.hash,
                    output.inputs.all()
                )))
            ),
            Output.objects.all()
        ))
        expected_outputs = set([
            # (<commitment>, <output_block_hash>, <spent>, <set_of_inputs<(block_hash)>>)
            # main outputs
            ('g1', self.to_hex('h100'), True, (self.to_hex('h101'), self.to_hex('h102.1'))),
            ('g2', self.to_hex('h100'), True, (self.to_hex('h101.1'), self.to_hex('h102'))),
            ('g3', self.to_hex('h100'), False, (self.to_hex('h102.1'),)),
            ('g4', self.to_hex('h100'), False, (self.to_hex('h101.1'),)),
            ('a', self.to_hex('h101'), False, tuple()),
            ('b', self.to_hex('h101'), True, (self.to_hex('h102'),)),
            ('c', self.to_hex('h102'), False, tuple()),
            ('d', self.to_hex('h102'), False, tuple()),

            # reorg 1 outputs
            ('d', self.to_hex('h101.1'), True, (self.to_hex('h102.1'),)),
            ('i', self.to_hex('h101.1'), False, tuple()),
            ('e', self.to_hex('h102.1'), False, tuple()),
            ('a', self.to_hex('h102.1'), False, tuple()),
            ('f', self.to_hex('h102.1'), False, tuple()),
        ])
        self.assertEqual(main_outputs, expected_outputs)

    def test_accepted_block_duplicate_view(self):
        """Test accepted-block view receives already stored block."""
        from backend.api.bootstrap import NodeV2API

        headers = [
            self._get_fake_header(1, 'h100', None),  # genesis
            self._get_fake_header(1, 'h100', None),  # genesis duplicate
        ]
        blocks = [
            self._get_fake_block(1, None, [], [
                self._get_output(1, 'g1', False),
            ]),  # genesis - h100
            self._get_fake_block(1, None, [], [
                self._get_output(1, 'g1', False),
            ]),  # duplicate block received
        ]
        # make sure node returns reorg data as defined in the function docs
        node_instance_mock = Mock()
        node_instance_mock.get_header.side_effect = headers
        node_instance_mock.get_block.side_effect = blocks
        self.nodeV2APIMock.return_value = node_instance_mock

        # send blocks, the first one is just to get it in db, the second one is
        # to test the duplicate one
        for i in range(len(blocks)):
            header = headers[i]
            post_data = self._get_accepted_block_data(
                header['height'], header['hash'], header['previous']
            )
            self.client.post(
                f'/api/blockchains/{self.blockchain.slug}/accepted/',
                json.dumps(post_data),
                content_type="application/json"
            )
        # validate correctness of the main chain block sequence
        main_chain_blocks = self.blockchain.blocks\
            .filter(reorg__isnull=True)\
            .order_by('height')
        expected_main_chain = [
            { 'height': 1, 'hash': self.to_hex('h100'), 'prev_hash': None },
        ]
        actual_main_chain = [
            {
                'height': block.height,
                'hash': block.hash,
                'prev_hash': block.prev_hash,
            }
            for block in main_chain_blocks
        ]
        self.assertEqual(actual_main_chain, expected_main_chain)

