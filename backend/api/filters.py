from django.conf import settings
from django.db.models import Count, F
from django_filters import rest_framework as filters
from rest_framework import filters as DRFfilters
from rest_framework.exceptions import APIException
from .models import Blockchain, Block, Node, NodeGroup, Reorg, Kernel, Output

import logging


logger = logging.getLogger(__name__)


class BlockFilter(filters.FilterSet):
    class Meta:
        model = Block
        fields = ('blockchain', 'height', 'hash')


class NodeFilter(filters.FilterSet):
    class Meta:
        model = Node
        fields = ('name', 'slug', 'archive')


class NodeGroupFilter(filters.FilterSet):
    class Meta:
        model = NodeGroup
        fields = ('name', 'slug')


class CustomBlockSearchFilter(DRFfilters.SearchFilter):
    """
    Alongside the given search_fields this filter filters also by:
    -  keyword 'reorgs' --> return only blocks where reorgs happened
    -  ['inputs', 'outputs', 'kernels'] ['=', '<', '>', '<=', '>='] [value] -->
       return only blocks matching this computation, eg: 'inputs > 2'
    You cannot combine different types of search (eg. 'reorgs' + 'computation')
    """

    def filter_queryset(self, request, queryset, view):
        queryset = super().filter_queryset(request, queryset, view)
        blockchain_slug = view.kwargs['blockchain_slug']
        original_search_terms = self.get_search_terms(request)
        search_terms = self._get_normalized_search_terms(original_search_terms)
        if len(search_terms) == 0:
            # searches:
            # - height --> add filter reorg=None
            # - hash --> nothing to add
            # - outputhash --> add filter reorg=None
            # - block-detail --> nothing to add
            # - block-list --> add filter reorg=None
            if len(original_search_terms) > 1:
                raise APIException('Too many standard search terms')
            if not original_search_terms:
                # it's either an unfiltered block-list or block-detail
                if view.action == 'list':
                    queryset = queryset.filter(reorg=None)
            else:
                # there's only 1 original search term, figure out which one
                if len(original_search_terms[0]) != 64:
                    # it's not block hash but either block height or output hash
                    # in both cases we need to filter out reorgs
                    queryset = queryset.filter(reorg=None)
            return queryset
        searched_types = set(map(lambda x: x['type'], search_terms))
        if len(searched_types) > 1:
            raise APIException('Cannot combine different types of searches')
        if searched_types == { 'reorgs' }:
            return self._get_reorgs_qs(blockchain_slug)
        elif searched_types == { 'computation' }:
            return self._get_computations_qs(search_terms, blockchain_slug)
        elif searched_types == { 'hash' }:
            return self._get_hash_qs(search_terms[0]['value'], blockchain_slug, queryset)
        elif searched_types == { 'height' }:
            return self._get_height_qs(search_terms[0]['value'], blockchain_slug)
        elif searched_types == { 'kernel_or_output' }:
            return self._get_kernel_or_output_qs(
                search_terms[0]['value'], blockchain_slug)
        else:
            logger.exception(
                'Invalid search terms',
                exc_info=e,
                extra={'search_terms': search_terms}
            )
            raise APIException('Invalid search terms')

    def _get_normalized_search_terms(self, search_terms):
        """
        Search terms of format ['outputs>1'] are not supported. Instead, the
        operators should be surrounded by spaces, eg. ['outputs', '>', '1'].
        Supported operators are ['=', '>', '<', '<=', '>=']
        """
        supported_operators = ['=', '>', '<', '<=', '>=']
        normalized_terms = []
        i = 0
        while i <= len(search_terms) - 1:
            if isinstance(search_terms[i], str) and search_terms[i].lower() in ['inputs', 'outputs', 'kernels']:
                operator = search_terms[i+1]
                if operator not in supported_operators:
                    raise APIException('Invalid search operator')
                value = int(search_terms[i+2])
                if value < 0:
                    raise APIException('Invalid search computation')
                normalized_terms.append({
                    'type': 'computation',
                    'source': search_terms[i],
                    'op': operator,
                    'value': value,
                })
                i += 3
            elif isinstance(search_terms[i], str) and search_terms[i].lower() == 'reorgs':
                normalized_terms.append({ 'type': 'reorgs' })
                i += 1
            elif len(search_terms[i]) == 64:
                # hash
                normalized_terms.append({
                    'type': 'hash',
                    'value': search_terms[i],
                })
                i += 1
            elif len(search_terms[i]) == 66:
                # kernel excess or output commitment
                normalized_terms.append({
                    'type': 'kernel_or_output',
                    'value': search_terms[i],
                })
                i += 1
            else:
                try:
                    value = int(search_terms[i])
                except ValueError:
                    value = None
                if value >= 0:
                    normalized_terms.append({
                        'type': 'height',
                        'value': value,
                    })
                    i += 1
                else:
                    # term which is not for this custom search, eg. block hash
                    i += 1
        return normalized_terms

    def _get_reorgs_qs(self, blockchain_slug):
        # NOTE: we first filter, then calculate reorg_len on filtered data and
        # then filter on annotated data that we've calculated
        reorg_heights = list(Reorg.objects\
            .select_related('start_main_block')\
            .filter(
                blockchain__slug=blockchain_slug,
                start_main_block__reorg=None,
            )\
            .annotate(reorg_len=F('end_reorg_block__height') - F('start_reorg_block__height') + 1)\
            .filter(reorg_len__gte=settings.MIN_REORG_LEN)\
            .values_list('start_main_block__height', flat=True)
        )
        queryset = Block.objects\
            .filter(
                blockchain__slug=blockchain_slug,
                reorg=None,
                height__in=reorg_heights,
            )\
            .order_by('-height')
        return queryset

    def _get_hash_qs(self, hash, blockchain_slug, queryset):
        return queryset.filter(
            blockchain__slug=blockchain_slug,
            hash=hash,
        )

    def _get_height_qs(self, height, blockchain_slug):
        return Block.objects.filter(
            blockchain__slug=blockchain_slug,
            height=height,
        )

    def _get_kernel_or_output_qs(self, kernel_or_output, blockchain_slug):
        kernel = Kernel.objects.filter(
            excess=kernel_or_output,
            block__blockchain__slug=blockchain_slug,
        ).first()
        if kernel:
            return Block.objects.filter(hash=kernel.block.hash)
        output = Output.objects.filter(
            commitment=kernel_or_output,
            block__blockchain__slug=blockchain_slug,
        ).first()
        if output:
            return Block.objects.filter(hash=output.block.hash)
        return Block.objects.none()

    def _get_computations_qs(self, search_terms, blockchain_slug):
        operator_mapping = {
            '=': '',
            '>': '__gt',
            '<': '__lt',
            '<=': '__lte',
            '>=': '__gte',
        }
        possible_sources = ['inputs', 'outputs', 'kernels']
        searched_sources = set(map(lambda x: x['source'], search_terms))
        op_searched_types = set(possible_sources) & set(searched_sources)
        op_qs = Blockchain.objects.get(slug=blockchain_slug).blocks.all()
        for search_term in search_terms:
            filters = {
                'blockchain__slug': blockchain_slug,
                'reorg': None,
            }
            op_map = operator_mapping[search_term['op']]
            filters[f'nr_{search_term["source"]}{op_map}'] = search_term['value']
            op_qs = op_qs.filter(**filters).order_by('-height')
        return op_qs

