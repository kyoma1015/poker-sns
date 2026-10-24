"""Opt-in journal recovery using separately trusted durable intent/CAS callbacks.

load/cas must authenticate an external private store, persist before returning,
compare the entire previous value atomically, and enforce finite call deadlines.
No local journal content supplies its own trust anchor. This module does not
connect a controller, claim a task, grant dispatch or reset finite run budgets.
"""
import hashlib
import re
from private_journal import PrivateJournal, _canonical


def _digest(index,previous,payload):
    return hashlib.sha256(_canonical({'index':index,'previous':previous,'payload':payload})).hexdigest()


def _head(value):
    return value is None or isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


class JournalCheckpoint:
    def __init__(self,journal,*,load,cas):
        if not isinstance(journal,PrivateJournal) or not callable(load) or not callable(cas):
            raise ValueError('journal and trusted external callbacks required')
        self.journal=journal;self.load=load;self.cas=cas

    def _state(self):
        state=self.load()
        if state is None:return None
        if not isinstance(state,dict) or set(state)!={'revision','head','pending'} or type(state['revision']) is not int or state['revision']<1 or not _head(state['head']):raise ValueError('invalid trusted pin state')
        pending=state['pending']
        if pending is not None:
            if not isinstance(pending,dict) or set(pending)!={'index','payload','digest'} or type(pending['index']) is not int or pending['index']<0 or not _head(pending['digest']) or pending['digest'] is None:raise ValueError('invalid trusted intent')
            if _digest(pending['index'],state['head'],pending['payload'])!=pending['digest']:raise ValueError('trusted intent digest mismatch')
        return state

    def _restore(self):
        state=self._state()
        if state is None:return self.journal.read(expected_head=None)
        pending=state['pending']
        if pending is None:return self.journal.read(expected_head=state['head'])
        self._operations([pending['payload']])
        target=pending['digest']
        try:
            values=self.journal.read(expected_head=target)
        except ValueError:
            values=self.journal.read(expected_head=state['head'])
            if len(values)!=pending['index']:raise ValueError('intent sequence mismatch')
            try:self.journal.append(pending['payload'],expected_head=state['head'])
            except ValueError:
                # Another recovery may have published the same trusted intent.
                self.journal.read(expected_head=target)
            values=self.journal.read(expected_head=target)
        if len(values)!=pending['index']+1 or values[-1]!=pending['payload']:raise ValueError('intent payload mismatch')
        committed={'revision':state['revision']+1,'head':target,'pending':None}
        if self.cas(state,committed) is not True and self._state()!=committed:raise ValueError('external pin CAS conflict')
        return values

    def restore(self):
        values=self._restore()
        self._operations(values)
        return [value['payload'] for value in values]

    def _operations(self,values):
        seen={}
        for value in values:
            if not isinstance(value,dict) or set(value)!={'operation_id','payload'} or not isinstance(value['operation_id'],str) or not 1<=len(value['operation_id'])<=128 or value['operation_id'] in seen:
                raise ValueError('invalid or duplicate journal operation')
            seen[value['operation_id']]=value['payload']
        return seen

    def append(self,payload,*,operation_id):
        _canonical(payload)
        if not isinstance(operation_id,str) or not 1<=len(operation_id)<=128:raise ValueError('bounded operation ID required')
        self.restore()
        state=self._state()
        if state is not None and state['pending'] is not None:raise ValueError('pending recovery required')
        head=state['head'] if state else None
        values=self.journal.read(expected_head=head)
        operations=self._operations(values)
        if operation_id in operations:
            if _canonical(operations[operation_id])!=_canonical(payload):raise ValueError('operation payload changed')
            return head
        payload={'operation_id':operation_id,'payload':payload}
        intent={'revision':state['revision']+1 if state else 1,'head':head,'pending':{'index':len(values),'payload':payload,'digest':_digest(len(values),head,payload)}}
        if self.cas(state,intent) is not True:raise ValueError('external intent CAS conflict')
        self.restore()
        return intent['pending']['digest']
