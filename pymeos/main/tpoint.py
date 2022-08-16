###############################################################################
#
# This MobilityDB code is provided under The PostgreSQL License.
#
# Copyright (c) 2019-2022, Université libre de Bruxelles and MobilityDB
# contributors
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose, without fee, and without a written 
# agreement is hereby granted, provided that the above copyright notice and
# this paragraph and the following two paragraphs appear in all copies.
#
# IN NO EVENT SHALL UNIVERSITE LIBRE DE BRUXELLES BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING
# LOST PROFITS, ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION,
# EVEN IF UNIVERSITE LIBRE DE BRUXELLES HAS BEEN ADVISED OF THE POSSIBILITY 
# OF SUCH DAMAGE.
#
# UNIVERSITE LIBRE DE BRUXELLES SPECIFICALLY DISCLAIMS ANY WARRANTIES, 
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE. THE SOFTWARE PROVIDED HEREUNDER IS ON
# AN "AS IS" BASIS, AND UNIVERSITE LIBRE DE BRUXELLES HAS NO OBLIGATIONS TO 
# PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS. 
#
###############################################################################

from __future__ import annotations

from abc import ABC
from ctypes import Union
from datetime import datetime
from typing import Optional, List, Literal

from dateutil.parser import parse
from postgis import Point, MultiPoint, LineString, GeometryCollection, MultiLineString

from pymeos_cffi.functions import tgeogpoint_in, tpoint_as_text, tgeompoint_in, tpoint_start_value, tpoint_end_value, \
    tpoint_values
from ..temporal import Temporal, TInstant, TInstantSet, TSequence, TSequenceSet


# Add method to Point to make the class hashable
def __hash__(self):
    return hash(self.values())


setattr(Point, '__hash__', __hash__)


class TPoint(Temporal, ABC):

    @property
    def start_value(self):
        return tpoint_start_value(self._inner)

    @property
    def end_value(self):
        return tpoint_end_value(self._inner)

    @property
    def values(self):
        values, count = tpoint_values(self._inner)
        return [values[i] for i in range(count)]

    def value_at_timestamp(self, timestamp):
        """
        Value at timestamp.
        """
        # TODO: Fix due to GSerialized problems
        # tpoint_value_at_timestamp()
        return None

    def __str__(self):
        return tpoint_as_text(self._inner, 3)


class TPointInst(TPoint, TInstant, ABC):
    """
    Abstract class for representing temporal points of instant subtype.
    """

    @property
    def value(self):
        """
        Geometry representing the values taken by the temporal value.
        """
        return self.values[0]


class TPointInstSet(TPoint, TInstantSet, ABC):
    """
    Abstract class for representing temporal points of instant set subtype.
    """

    @property
    def values(self):
        """
        Geometry representing the values taken by the temporal value.
        """
        values = super().values
        return MultiPoint(values)


class TPointSeq(TSequence, ABC):
    """
    Abstract class for representing temporal points of sequence subtype.
    """

    __slots__ = ['_inner']

    @property
    def values(self):
        """
        Geometry representing the values taken by the temporal value.
        """
        values = [inst._value for inst in self._instantList]
        result = values[0] if len(values) == 1 else LineString(values)
        return result


class TPointSeqSet(TSequenceSet, ABC):
    """
    Abstract class for representing temporal points of sequence set subtype.
    """

    @property
    def values(self):
        """
        Geometry representing the values taken by the temporal value.
        """
        values = [seq.values for seq in self._sequenceList]
        points = [geo for geo in values if isinstance(geo, Point)]
        lines = [geo for geo in values if isinstance(geo, LineString)]
        if len(points) != 0 and len(points) != 0:
            return GeometryCollection(points + lines)
        if len(points) != 0 and len(points) == 0:
            return MultiPoint(points)
        if len(points) == 0 and len(points) != 0:
            return MultiLineString(lines)


class TGeomPoint(TPoint, ABC):
    """
    Abstract class for representing temporal geometric or geographic points of any subtype.
    """

    BaseClass = Point
    BaseClassDiscrete = False
    _parse_function = tgeompoint_in

    @staticmethod
    def read_from_cursor(value, cursor=None):
        if not value:
            return None
        if value.startswith('Interp=Stepwise;'):
            value1 = value.replace('Interp=Stepwise;', '')
            if value1[0] == '{':
                return TGeomPointSeqSet(string=value)
            else:
                return TGeomPointSeq(string=value)
        elif value[0] != '{' and value[0] != '[' and value[0] != '(':
            return TGeomPointInst(string=value)
        elif value[0] == '[' or value[0] == '(':
            return TGeomPointSeq(string=value)
        elif value[0] == '{':
            if value[1] == '[' or value[1] == '(':
                return TGeomPointSeqSet(string=value)
            else:
                return TGeomPointInstSet(string=value)
        raise Exception("ERROR: Could not parse temporal point value")

    @staticmethod
    def write(value):
        if not isinstance(value, TGeomPoint):
            raise ValueError('Value must an instance of a subclass of TGeomPoint')
        return value.__str__().strip("'")

    @property
    def hasz(self):
        """
        Does the temporal point has Z dimension?
        """
        return self.start_value.z is not None

    @property
    def srid(self):
        """
        Returns the SRID.
        """
        result = self.start_value.srid if hasattr(self.start_value, "srid") else None
        return result


class TGeogPoint(TPoint, ABC):
    """
    Abstract class for representing temporal geographic points of any subtype.
    """

    BaseClass = Point
    BaseClassDiscrete = False
    _parse_function = tgeogpoint_in

    @staticmethod
    def read_from_cursor(value, cursor=None):
        if not value:
            return None
        if value.startswith('Interp=Stepwise;'):
            value1 = value.replace('Interp=Stepwise;', '')
            if value1[0] == '{':
                return TGeogPointSeqSet(string=value)
            else:
                return TGeogPointSeq(string=value)
        elif value[0] != '{' and value[0] != '[' and value[0] != '(':
            return TGeogPointInst(string=value)
        elif value[0] == '[' or value[0] == '(':
            return TGeogPointSeq(string=value)
        elif value[0] == '{':
            if value[1] == '[' or value[1] == '(':
                return TGeogPointSeqSet(string=value)
            else:
                return TGeogPointInstSet(string=value)
        raise Exception("ERROR: Could not parse temporal point value")

    @staticmethod
    def write(value):
        if not isinstance(value, TGeogPoint):
            raise ValueError('Value must an instance of a subclass of TGeogPoint')
        return value.__str__().strip("'")

    @property
    def hasz(self):
        """
        Does the temporal point has Z dimension?
        """
        return self.start_value.z is not None

    @property
    def srid(self):
        """
        Returns the SRID.
        """
        result = self.start_value.srid if hasattr(self.start_value, "srid") else None
        return result


class TGeomPointInst(TPointInst, TGeomPoint):
    """
    Class for representing temporal geometric points of instant subtype.

    ``TGeomPointInst`` objects can be created with a single argument of type
    string as in MobilityDB.

        >>> TGeomPointInst('Point(10.0 10.0)@2019-09-01')
        >>> TGeomPointInst('SRID=4326,Point(10.0 10.0)@2019-09-01')

    Another possibility is to give the ``value`` and the ``time`` arguments,
    which can be instances of ``str``, ``Point`` or ``datetime``.
    Additionally, the SRID can be specified, it will be 0 by default if not
    given.

        >>> TGeomPointInst('Point(10.0 10.0)', '2019-09-08 00:00:00+01', 4326)
        >>> TGeomPointInst(['Point(10.0 10.0)', '2019-09-08 00:00:00+01', 4326])
        >>> TGeomPointInst(Point(10.0, 10.0), parse('2019-09-08 00:00:00+01'), 4326)
        >>> TGeomPointInst([Point(10.0, 10.0), parse('2019-09-08 00:00:00+01'), 4326])

    """

    _make_function = lambda *args: None
    _cast_function = lambda x: None

    def __init__(self, *, string: Optional[str] = None, point: Optional[Union[str, Point]] = None,
                 timestamp: Optional[Union[str, datetime]] = None, srid: Optional[int] = 0, _inner=None) -> None:
        super().__init__(string=string, value=point, timestamp=timestamp, _inner=_inner)
        if self._inner is None:
            self._inner = tgeompoint_in(f"SRID={srid};{point}@{timestamp}")


class TGeogPointInst(TPointInst, TGeogPoint):
    """
    Class for representing temporal geographic points of instant subtype.

    ``TGeogPointInst`` objects can be created with a single argument of type
    string as in MobilityDB.

        >>> TGeogPointInst(string='Point(10.0 10.0)@2019-09-01')

    Another possibility is to give the ``value`` and the ``time`` arguments,
    which can be instances of ``str``, ``Point`` or ``datetime``.
    Additionally, the SRID can be specified, it will be 0 by default if not
    given.

        >>> TGeogPointInst(point='Point(10.0 10.0)',timestamp='2019-09-08 00:00:00+01')
        >>> TGeogPointInst(point=Point(10.0, 10.0),timestamp=parse('2019-09-08 00:00:00+01'))

    """

    _make_function = lambda *args: None
    _cast_function = lambda x: None

    def __init__(self, *, string: Optional[str] = None, point: Optional[Union[str, Point]] = None,
                 timestamp: Optional[Union[str, datetime]] = None, srid: Optional[int] = 0, _inner=None) -> None:
        super().__init__(string=string, value=point, timestamp=timestamp, _inner=_inner)
        if self._inner is None:
            self._inner = tgeogpoint_in(f"SRID={srid};{point}@{timestamp}")


class TGeomPointInstSet(TPointInstSet, TGeomPoint):
    """
    Class for representing temporal geometric points of instant set subtype.

    ``TGeomPointInstSet`` objects can be created with a single argument of type
    string as in MobilityDB.

        >>> TGeomPointInstSet('Point(10.0 10.0)@2019-09-01')

    Another possibility is to give a tuple or list of arguments specifying
    the composing instants, which can be instances of ``str`` or
    ``TGeomPointInst``.

        >>> TGeomPointInstSet('Point(10.0 10.0)@2019-09-01 00:00:00+01', 'Point(20.0 20.0)@2019-09-02 00:00:00+01', 'Point(10.0 10.0)@2019-09-03 00:00:00+01')
        >>> TGeomPointInstSet(TGeomPointInst('Point(10.0 10.0)@2019-09-01 00:00:00+01'), TGeomPointInst('Point(20.0 20.0)@2019-09-02 00:00:00+01'), TGeomPointInst('Point(10.0 10.0)@2019-09-03 00:00:00+01'))
        >>> TGeomPointInstSet(['Point(10.0 10.0)@2019-09-01 00:00:00+01', 'Point(20.0 20.0)@2019-09-02 00:00:00+01', 'Point(10.0 10.0)@2019-09-03 00:00:00+01'])
        >>> TGeomPointInstSet([TGeomPointInst('Point(10.0 10.0)@2019-09-01 00:00:00+01'), TGeomPointInst('Point(20.0 20.0)@2019-09-02 00:00:00+01'), TGeomPointInst('Point(10.0 10.0)@2019-09-03 00:00:00+01')])

    """

    ComponentClass = TGeomPointInst

    def __init__(self, *, string: Optional[str] = None, instant_list: Optional[List[Union[str, TGeomPointInst]]] = None,
                 merge: bool = True, _inner=None):
        super().__init__(string=string, instant_list=instant_list, merge=merge, _inner=_inner)


class TGeogPointInstSet(TPointInstSet, TGeogPoint):
    """
    Class for representing temporal geometric points of instant set subtype.

    ``TGeogPointInstSet`` objects can be created with a single argument of type
    string as in MobilityDB.

        >>> TGeogPointInstSet('Point(10.0 10.0)@2019-09-01')

    Another possibility is to give a tuple or list of arguments specifying
    the composing instants, which can be instances of ``str`` or
    ``TGeogPointInst``.

        >>> TGeogPointInstSet('Point(10.0 10.0)@2019-09-01 00:00:00+01', 'Point(20.0 20.0)@2019-09-02 00:00:00+01', 'Point(10.0 10.0)@2019-09-03 00:00:00+01')
        >>> TGeogPointInstSet(TGeogPointInst(string='Point(10.0 10.0)@2019-09-01 00:00:00+01'), TGeogPointInst(string='Point(20.0 20.0)@2019-09-02 00:00:00+01'), TGeogPointInst(string='Point(10.0 10.0)@2019-09-03 00:00:00+01'))
        >>> TGeogPointInstSet(['Point(10.0 10.0)@2019-09-01 00:00:00+01', 'Point(20.0 20.0)@2019-09-02 00:00:00+01', 'Point(10.0 10.0)@2019-09-03 00:00:00+01'])
        >>> TGeogPointInstSet([TGeogPointInst(string='Point(10.0 10.0)@2019-09-01 00:00:00+01'), TGeogPointInst(string='Point(20.0 20.0)@2019-09-02 00:00:00+01'), TGeogPointInst(string='Point(10.0 10.0)@2019-09-03 00:00:00+01')])

    """

    ComponentClass = TGeogPointInst

    def __init__(self, *, string: Optional[str] = None, instant_list: Optional[List[Union[str, TGeogPointInst]]] = None,
                 merge: bool = True, _inner=None):
        super().__init__(string=string, instant_list=instant_list, merge=merge, _inner=_inner)


class TGeomPointSeq(TPointSeq, TGeomPoint):
    """
    Class for representing temporal geometric points of sequence subtype.

    ``TGeomPointSeq`` objects can be created with a single argument of type
    string as in MobilityDB.

        >>> TGeomPointSeq('[Point(10.0 10.0)@2019-09-01 00:00:00+01, Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')
        >>> TGeomPointSeq('Interp=Stepwise;[Point(10.0 10.0)@2019-09-01 00:00:00+01, Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')

    Another possibility is to give the arguments as follows:

    * ``instantList`` is the list of composing instants, which can be instances
      of ``str`` or ``TGeogPointInst``,
    * ``lower_inc`` and ``upper_inc`` are instances of ``bool`` specifying
      whether the bounds are inclusive or not,  where by default '`lower_inc``
      is ``True`` and ``upper_inc`` is ``False``,
    * ``interp`` which is either ``'Linear'`` or ``'Stepwise'``, the former
      being the default, and
    * ``srid`` is an integer specifiying the SRID

    Some examples are shown next.

        >>> TGeomPointSeq(['Point(10.0 10.0)@2019-09-01 00:00:00+01', 'Point(20.0 20.0)@2019-09-02 00:00:00+01', 'Point(10.0 10.0)@2019-09-03 00:00:00+01'])
        >>> TGeomPointSeq([TGeomPointInst('Point(10.0 10.0)@2019-09-01 00:00:00+01'), TGeomPointInst('Point(20.0 20.0)@2019-09-02 00:00:00+01'), TGeomPointInst('Point(10.0 10.0)@2019-09-03 00:00:00+01')])
        >>> TGeomPointSeq(['Point(10.0 10.0)@2019-09-01 00:00:00+01', 'Point(20.0 20.0)@2019-09-02 00:00:00+01', 'Point(10.0 10.0)@2019-09-03 00:00:00+01'], True, True, 'Stepwise')
        >>> TGeomPointSeq([TGeomPointInst('Point(10.0 10.0)@2019-09-01 00:00:00+01'), TGeomPointInst('Point(20.0 20.0)@2019-09-02 00:00:00+01'), TGeomPointInst('Point(10.0 10.0)@2019-09-03 00:00:00+01')], True, True, 'Stepwise')

    """

    ComponentClass = TGeomPointInst

    def __init__(self, *, string: Optional[str] = None, instant_list: Optional[List[Union[str, TGeomPointInst]]] = None,
                 lower_inc: bool = True, upper_inc: bool = False, interp: Literal['Linear', 'Stepwise'] = 'Linear',
                 normalize: bool = True, _inner=None):
        super().__init__(string=string, instant_list=instant_list, lower_inc=lower_inc, upper_inc=upper_inc,
                         normalize=normalize, _inner=_inner)


class TGeogPointSeq(TPointSeq, TGeogPoint):
    """
    Class for representing temporal geographic points of sequence subtype.

    ``TGeogPointSeq`` objects can be created with a single argument of type
    string as in MobilityDB.

        >>> TGeogPointSeq('[Point(10.0 10.0)@2019-09-01 00:00:00+01, Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')
        >>> TGeogPointSeq('Interp=Stepwise;[Point(10.0 10.0)@2019-09-01 00:00:00+01, Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')

    Another possibility is to give the arguments as follows:

    * ``instantList`` is the list of composing instants, which can be instances
      of ``str`` or ``TGeogPointInst``,
    * ``lower_inc`` and ``upper_inc`` are instances of ``bool`` specifying
      whether the bounds are includive or not,  where by default '`lower_inc``
      is ``True`` and ``upper_inc`` is ``False``, and
    * ``interp`` which is either ``'Linear'`` or ``'Stepwise'``, the former
      being the default.
    * ``srid`` is an integer specifiying the SRID

    Some examples are shown next.

        >>> TGeogPointSeq(['Point(10.0 10.0)@2019-09-01 00:00:00+01', 'Point(20.0 20.0)@2019-09-02 00:00:00+01', 'Point(10.0 10.0)@2019-09-03 00:00:00+01'])
        >>> TGeogPointSeq([TGeogPointInst(string='Point(10.0 10.0)@2019-09-01 00:00:00+01'), TGeogPointInst(string='Point(20.0 20.0)@2019-09-02 00:00:00+01'), TGeogPointInst(string='Point(10.0 10.0)@2019-09-03 00:00:00+01')])
        >>> TGeogPointSeq(['Point(10.0 10.0)@2019-09-01 00:00:00+01', 'Point(20.0 20.0)@2019-09-02 00:00:00+01', 'Point(10.0 10.0)@2019-09-03 00:00:00+01'], True, True, 'Stepwise')
        >>> TGeogPointSeq([TGeogPointInst(string='Point(10.0 10.0)@2019-09-01 00:00:00+01'), TGeogPointInst(string='Point(20.0 20.0)@2019-09-02 00:00:00+01'), TGeogPointInst(string='Point(10.0 10.0)@2019-09-03 00:00:00+01')], True, True, 'Stepwise')

    """

    ComponentClass = TGeogPointInst

    def __init__(self, *, string: Optional[str] = None, instant_list: Optional[List[Union[str, TGeogPointInst]]] = None,
                 lower_inc: bool = True, upper_inc: bool = False, interp: Literal['Linear', 'Stepwise'] = 'Linear',
                 normalize: bool = True, _inner=None):
        super().__init__(string=string, instant_list=instant_list, lower_inc=lower_inc, upper_inc=upper_inc,
                         normalize=normalize, _inner=_inner)


class TGeomPointSeqSet(TPointSeqSet, TGeomPoint):
    """
    Class for representing temporal geometric points of sequence subtype.

    ``TGeomPointSeqSet`` objects can be created with a single argument of type
    string as in MobilityDB.

        >>> TGeomPointSeqSet('{[Point(10.0 10.0)@2019-09-01 00:00:00+01], [Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]}')
        >>> TGeomPointSeqSet('Interp=Stepwise;{[Point(10.0 10.0)@2019-09-01 00:00:00+01], [Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]}')

    Another possibility is to give the arguments as follows:

    * ``sequenceList`` is the list of composing sequences, which can be instances
      of ``str`` or ``TGeomPointSeq``,
    * ``interp`` can be ``'Linear'`` or ``'Stepwise'``, the former being
      the default, and
    * ``srid`` is an integer specifiying the SRID, if will be 0 by default if
      not given.

    Some examples are shown next.

        >>> TGeomPointSeqSet(['[Point(10.0 10.0)@2019-09-01 00:00:00+01]', '[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]'])
        >>> TGeomPointSeqSet(['[Point(10.0 10.0)@2019-09-01 00:00:00+01]', '[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]'], 'Linear')
        >>> TGeomPointSeqSet(['Interp=Stepwise;[Point(10.0 10.0)@2019-09-01 00:00:00+01]', 'Interp=Stepwise;[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]'], 'Stepwise')
        >>> TGeomPointSeqSet([TGeomPointSeq('[Point(10.0 10.0)@2019-09-01 00:00:00+01]'), TGeomPointSeq('[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')])
        >>> TGeomPointSeqSet([TGeomPointSeq('[Point(10.0 10.0)@2019-09-01 00:00:00+01]'),  TGeomPointSeq('[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')], 'Linear')
        >>> TGeomPointSeqSet([TGeomPointSeq('Interp=Stepwise;[Point(10.0 10.0)@2019-09-01 00:00:00+01]'), TGeomPointSeq('Interp=Stepwise;[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')], 'Stepwise')

    """

    ComponentClass = TGeomPointSeq

    def __init__(self, *, string: Optional[str] = None, sequence_list: Optional[List[Union[str, TGeomPointSeq]]] = None,
                 normalize: bool = True, _inner=None):
        super().__init__(string=string, sequence_list=sequence_list, normalize=normalize, _inner=_inner)


class TGeogPointSeqSet(TPointSeqSet, TGeogPoint):
    """
    Class for representing temporal geographic points of sequence subtype.

    ``TGeogPointSeqSet`` objects can be created with a single argument of type string
    as in MobilityDB.

        >>> TGeogPointSeqSet('{[Point(10.0 10.0)@2019-09-01 00:00:00+01], [Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]}')
        >>> TGeogPointSeqSet('Interp=Stepwise;{[Point(10.0 10.0)@2019-09-01 00:00:00+01], [Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]}')

    Another possibility is to give the arguments as follows:

    * ``sequenceList`` is the list of composing sequences, which can be instances
      of ``str`` or ``TGeogPointSeq``,
    * ``interp`` can be ``'Linear'`` or ``'Stepwise'``, the former being
      the default, and
    * ``srid`` is an integer specifiying the SRID, if will be 0 by default if
      not given.

    Some examples are shown next.

        >>> TGeogPointSeqSet(['[Point(10.0 10.0)@2019-09-01 00:00:00+01]', '[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]'])
        >>> TGeogPointSeqSet(['[Point(10.0 10.0)@2019-09-01 00:00:00+01]', '[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]'], 'Linear')
        >>> TGeogPointSeqSet(['Interp=Stepwise;[Point(10.0 10.0)@2019-09-01 00:00:00+01]', 'Interp=Stepwise;[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]'], 'Stepwise')
        >>> TGeogPointSeqSet([TGeogPointSeq('[Point(10.0 10.0)@2019-09-01 00:00:00+01]'), TGeogPointSeq('[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')])
        >>> TGeogPointSeqSet([TGeogPointSeq('[Point(10.0 10.0)@2019-09-01 00:00:00+01]'),  TGeogPointSeq('[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')], 'Linear')
        >>> TGeogPointSeqSet([TGeogPointSeq('Interp=Stepwise;[Point(10.0 10.0)@2019-09-01 00:00:00+01]'), TGeogPointSeq('Interp=Stepwise;[Point(20.0 20.0)@2019-09-02 00:00:00+01, Point(10.0 10.0)@2019-09-03 00:00:00+01]')], 'Stepwise')

    """

    ComponentClass = TGeogPointSeq

    def __init__(self, *, string: Optional[str] = None, sequence_list: Optional[List[Union[str, TGeogPointSeq]]] = None,
                 normalize: bool = True, _inner=None):
        super().__init__(string=string, sequence_list=sequence_list, normalize=normalize, _inner=_inner)