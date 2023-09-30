from __future__ import annotations

from typing import Union, overload, Optional, TYPE_CHECKING

from pymeos_cffi import intspanset_in, intspanset_out

from pymeos.collections import SpanSet

if TYPE_CHECKING:
    from .intspan import IntSpan

class IntSpanSet(SpanSet[int]):
    """
    Class for representing lists of disjoint intspans.

    ``IntSpanSet`` objects can be created with a single argument of type string
    as in MobilityDB.

        >>> IntSpanSet(string='{[8, 10], [11, 1]}')

    Another possibility is to give a list specifying the composing
    spans, which can be instances  of ``str`` or ``IntSpan``. The composing
    spans must be given in increasing order.

        >>> IntSpanSet(span_list=['[8, 10]', '[11, 12]'])
        >>> IntSpanSet(span_list=[IntSpan('[8, 10]'), IntSpan('[11, 12]')])

    """

    __slots__ = ['_inner']

    _mobilitydb_name = 'intspanset'

    _parse_function = intspanset_in
    _parse_value_function = lambda span: intspanset_in(span)[0] if isinstance(spanset, str) else intspanset_in._inner[0]


    # ------------------------- Output ----------------------------------------
    def __str__(self):
        """
        Return the string representation of the content of ``self``.

        Returns:
            A new :class:`str` instance

        MEOS Functions:
            intspanset_out
        """
        return intspanset_out(self._inner)

    # ------------------------- Conversions -----------------------------------

    def to_span(self) -> IntSpan:
        """
        Returns a span that encompasses ``self``.

        Returns:
            A new :class:`IntSpan` instance

        MEOS Functions:
            spanset_span
        """
        from .intspan import IntSpan
        return IntSpan(_inner=super().to_span())

    # ------------------------- Accessors -------------------------------------
    def start_span(self) -> IntSpan:
        """
        Returns the first span in ``self``.
        Returns:
            A :class:`IntSpan` instance

        MEOS Functions:
            spanset_start_span
        """
        from .intspan import IntSpan
        return IntSpan(_inner=super().start_span())

    def end_span(self) -> IntSpan:
        """
        Returns the last span in ``self``.
        Returns:
            A :class:`IntSpan` instance

        MEOS Functions:
            spanset_end_span
        """
        from .intspan import IntSpan
        return IntSpan(_inner=super().end_span())

    def span_n(self, n: int) -> IntSpan:
        """
        Returns the n-th span in ``self``.
        Returns:
            A :class:`IntSpan` instance

        MEOS Functions:
            spanset_span_n
        """
        from .intspan import IntSpan
        return IntSpan(_inner=super().span_n(n))

    def spans(self) -> List[IntSpan]:
        """
        Returns the list of spans in ``self``.
        Returns:
            A :class:`list[IntSpan]` instance

        MEOS Functions:
            spanset_spans
        """
        from .intspan import IntSpan
        ps = super().spans()
        return [IntSpan(_inner=ps[i]) for i in range(self.num_spans())]


    # ------------------------- Set Operations --------------------------------
    @overload
    def intersection(self, other: IntSpan) -> IntSpanSet:
        ...

    @overload
    def intersection(self, other: IntSpanSet) -> IntSpanSet:
        ...

    @overload
    def intersection(self, other: int) -> int:
        ...

    def intersection(self, other: Union[int, IntSpan, IntSpanSet]) -> Union[int, IntSpanSet]:
        """
        Returns the intersection of ``self`` and ``other``.

        Args:
            other: object to intersect with

        Returns:
            An int or a :class:`IntSpanSet` instance. The actual class depends
            on ``other``.

        MEOS Functions:
            intersection_intspanset_int, intersection_spanset_spanset,
            intersection_spanset_span
        """
        from .intspan import IntSpan
        if isinstance(other, int):
            result = intersection_intspanset_int(self._inner, int)
            return timestamptz_to_int(result) if result is not None else None
        elif isinstance(other, TimestampSet):
            result = super().intersection(other)
            return TimestampSet(_inner=result) if result is not None else None
        elif isinstance(other, IntSpan):
            result = super().intersection(other)
            return IntSpanSet(_inner=result) if result is not None else None
        elif isinstance(other, IntSpanSet):
            result = super().intersection(other)
            return IntSpanSet(_inner=result) if result is not None else None
        else:
            raise TypeError(f'Operation not supported with type {other.__class__}')

    def __mul__(self, other):
        """
        Returns the intersection of ``self`` and ``other``.

        Args:
            other: object to intersect with

        Returns:
            A :class:`Time` instance. The actual class depends on ``other``.

        MEOS Functions:
            intersection_intspanset_int, intersection_spanset_spanset,
            intersection_spanset_span
        """
        return self.intersection(other)

    def minus(self, other: Time) -> IntSpanSet:
        """
        Returns the difference of ``self`` and ``other``.

        Args:
            other: object to diff with

        Returns:
            A :class:`IntSpanSet` instance.

        MEOS Functions:
            minus_spanset_span, minus_spanset_spanset, minus_intspanset_int
        """
        if isinstance(other, int):
            result = minus_intspanset_int(self._inner, int)
        else:
            result = super().minus(other)
        return IntSpanSet(_inner=result) if result is not None else None

    def __sub__(self, other):
        """
        Returns the difference of ``self`` and ``other``.

        Args:
            other: object to diff with

        Returns:
            A :class:`IntSpanSet` instance.

        MEOS Functions:
            minus_spanset_span, minus_spanset_spanset,
            minus_intspanset_int
        """
        return self.minus(other)

    def union(self, other: Time) -> IntSpanSet:
        """
        Returns the union of ``self`` and ``other``.

        Args:
            other: object to merge with

        Returns:
            A :class:`IntSpanSet` instance.

        MEOS Functions:
            union_intspanset_int, union_spanset_spanset,
            union_spanset_span
        """
        if isinstance(other, int):
            result = union_intspanset_int(self._inner, int)
        else:
            result = super().union(other)
        return IntSpanSet(_inner=result) if result is not None else None

    def __add__(self, other):
        """
        Returns the union of ``self`` and ``other``.

        Args:
            other: object to merge with

        Returns:
            A :class:`IntSpanSet` instance.

        MEOS Functions:
            union_intspanset_int, union_spanset_spanset,
            union_spanset_span
        """
        return self.union(other)

