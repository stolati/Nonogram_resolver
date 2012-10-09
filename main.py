#!/usr/bin/env python3

from itertools import *
from functools import reduce



class CellState:
  UNKNOWN = -1
  EMPTY = 0
  FULL = 1


class Cell:
  """Represent a single case of an array
     have 3 states : empty, really empty, full"""


  def __init__(self, state = CellState.UNKNOWN):
    self.state = state

  def setState(self, state): self.state = state
  def getState(self, state): return self.state

  #def __str__(self): return {CellState.UNKNOWN:'X', CellState.EMPTY:'.', CellState.FULL:'.'}[self.state]
  def __str__(self): return {CellState.UNKNOWN:'.', CellState.EMPTY:'_', CellState.FULL:'X'}[self.state]
  def __repr__(self): return str(self)

  @staticmethod
  def areCompatible(s1, s2):
    if s1.state == s2.state: return True
    if s1.state == CellState.UNKNOWN: return True
    if s2.state == CellState.UNKNOWN: return True
    return False

  @staticmethod
  def getCommon(s1, s2):
    if not Cell.areCompatible(s1, s2): return CellUnknown
    return s1

  def apply_on_me(self, c):
    if self.state == CellState.UNKNOWN:
      self.state = c.state
      return True
    return False


#static values cells
class StaticValueCell(Cell):
  def setState(self, state): pass

CellUnknown = StaticValueCell(CellState.UNKNOWN)
CellEmpty = StaticValueCell(CellState.EMPTY)
CellFull = StaticValueCell(CellState.FULL)





class LineCol:
  """
  Represent a line or a column
  Have a size, can give all solution in it
  """

  def __init__(self, elements, numbers):
    """
    Take a list of Cell
    Thoses case can be used by others classes
    """
    self.size = len(elements)
    self.content = list(elements)
    self.numbers = list(numbers)
    self.isFull = False

  def test_next(self):
    """Test for each possibilty of the LineCol
    then, if some elements are the same for some,
    change the inside CellState of thoses, making them static
    return true if at least one cell have changed
    """
    if self.isFull : return False

    #print('test_next', self.size, self.content)

    validElements = self.getListValidElements()
    #print(validElements)
    if not validElements : return False

    validWithMe = list(filter(self.isGoodWithMe, validElements))
    #print("validWithMe : ", validWithMe)
    if not validWithMe : return False

    commons = list(map(self.compareCells, *validWithMe))
    #print("commons:", commons)

    changed = False
    self.isFull = True
    for me, res in zip(self.content, commons):
      if me.state != CellState.UNKNOWN:
        assert me.state == res.state
        continue
      if res.state == CellState.UNKNOWN:
        self.isFull = False
        continue
      me.state = res.state
      changed = True

    return changed


  def compareCells(self, *cells): return reduce(Cell.getCommon, cells)


  def isGoodWithMe(self, state):
    assert len(state) == self.size
    return all(map(Cell.areCompatible, state, self.content))



  def getListValidElements(self):
    """Return a list of valid line col"""
    return list(chain(self.genFull(self.size, self.numbers), self.genEmpty(self.size, self.numbers)))


  def genEmpty(self, left, numbers):
    if not numbers: return [repeat(CellEmpty, left)] #no number left, fill all
    if left < 1:
      if not numbers: return [[]] #no elements left, return empty 
      if numbers : return []

    res = []
    for i in range(1, left):
      newState = list(repeat(CellEmpty, i))
      #print('genEmpty', left, numbers, 'loop for', i, '=>', newState)

      for subState in self.genFull(left - i, numbers):
        #print('genEmpty', left, numbers, '  have subState', list(subState))
        res.append( list(chain(list(newState), list(subState)))  )

    #print('genEmpty', left, numbers, '=>', res)
    return res


  def genFull(self, left, numbers):
    if left < 1 or not numbers:
      #print('genFull', left, numbers, '=>', [])
      return []

    next_num = numbers[0]
    if next_num > left :
      #print('genFull', left, numbers, '=>', [])
      return []

    res = []
    newState = list(repeat(CellFull, next_num))
    for subState in self.genEmpty(left - next_num, numbers[1:]):
      res.append( list(chain(list(newState), subState) ))

    #print('genFull', left, numbers, '=>', res)
    return res







class ArrayField:
  """Represent the full array, list of lines and collumns"""

  def __init__(self, specs):
    self.colsSpecs, self.lineSpecs = specs.toList()

    self.field = [[Cell() for c in self.colsSpecs] for l in self.lineSpecs]

    self.lines = [LineCol(line, self.lineSpecs[num]) for num, line in enumerate(self.field)]
    self.cols = [
        LineCol([line[i] for line in self.field], self.colsSpecs[i])
        for i in range(len(self.field[0]))
    ]

  def loopOn(self, hook_obj):
    changed = True
    hook_obj.begin(self)

    isFirst = True #beause it should at least try to do both the first time

    while changed:

      changed = False
      for c in self.cols:
        if c.test_next():
          hook_obj.changed(self)
          changed = True
      hook_obj.done_cols(self)
      if changed == False and not isFirst : break

      changed = False
      for l in self.lines:
        if l.test_next():
          hook_obj.changed(self)
          changed = True
      hook_obj.done_lines(self)

      isFirst = False

    hook_obj.end(self)


  def __str__(self):
    res = ''
    for l in self.field:
      for c in l:
        res += ' ' + str(c)
      res += "\n"
    return res


class SpecReader:
  """Read specs in multiples format"""
  def __init__(self, specs):


    self.specs = [
      [
        [
          self._numStr2num(numList)
          for numList in self._numListStr2list(numListList)]
        for numListList in self._colineStr2list(colline)
      ]
      for colline in self._mainStr2list(specs)
    ]

  def _mainStr2list(self, s):
    if not isinstance(s, str): return s
    return [ss for ss in s.split('\n') if ss]

  def _colineStr2list(self, s):
    if not isinstance(s, str): return s
    return [ss for ss in s.split(',') if ss]

  def _numListStr2list(self, s):
    if not isinstance(s, str): return s
    return [ss for ss in s.split(' ') if ss]

  def _numStr2num(self, s):
    if not isinstance(s, str): return s
    return int(s)


  def toList(self): return self.specs



class loopHook:
  def begin(self, arrField): pass
  def end(self, arrField): pass
  def changed(self, arrField): pass
  def done_cols(self, arrField): pass
  def changed(self, arrField): pass
  def done_lines(self, arrField): pass


class loopHookKeyboard(loopHook):
  def _act(self, arrField):
    print(arrField)
    input()

  def begin(self, arrField):  self._act(arrField)
  def changed(self, arrField): self._act(arrField)


class loopHookKeyboardBigStep(loopHook):

  def _act(self, arrField, els):
    print('step','=', els)
    print(arrField)
    input()

  def begin(self, arrField):  self._act(arrField, 'begin')
  def done_cols(self, arrField): self._act(arrField, 'lines')
  def done_lines(self, arrField): self._act(arrField, 'cols')

class loopHookWhole(loopHook):
  def end(self, arrField): print(arrField)


if __name__ == "__main__":
  import maps
  m = maps.maps["Nemo Pictures"]["medium"]
  m = maps.maps["NonoSparks Genesis"]

  for k in sorted(m):
    af = ArrayField(SpecReader(m[k]))
    af.loopOn(loopHookWhole())

  #af.loopOne()
  #af.loopOne()
  #print(af)


#__EOF__
