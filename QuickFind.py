import numpy as np

class QuickUnionUF:
    size = 0
    cid = None
    noOfUnion = 0
   
    def union(self, p, q):
        if self.find(p, q): return
        self.noOfUnion += 1
        if self.noOfUnion % 100000 == 0:
            print('union called', self.noOfUnion)
        rp = self._root_(p)
        rq = self._root_(q)
        self.cid[rp] = rq
    def _root_(self, p):
        while p != self.cid[p]:
            self.cid[p] = self.cid[self.cid[p]]
            p = self.cid[p]
        return p
    def find(self, p, q):
        return self._root_(p) == self._root_(q)
    def __init__(self, n):
        self.size = n
        self.cid = np.zeros(self.size, dtype=np.int32)
        for i in range(self.size):
            self.cid[i] = i