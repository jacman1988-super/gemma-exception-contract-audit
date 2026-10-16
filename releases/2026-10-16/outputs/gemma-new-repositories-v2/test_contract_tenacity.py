"""Additional local controls: added after reference runs, before reading model output."""
import asyncio
import pytest
from tenacity import Retrying,AsyncRetrying,RetryCallState

class FalseWait:
    def __bool__(self):return False
    def __call__(self,state):return 1.25

class EmptyWait(list):
    def __call__(self,state):return .75

@pytest.mark.parametrize('strategy,expected',[(None,0),(0,0),(FalseWait(),1.25),(EmptyWait(),.75)])
@pytest.mark.parametrize('async_mode',[False,True])
def test_wait_contract(strategy,expected,async_mode):
    retry=(AsyncRetrying if async_mode else Retrying)(wait=strategy)
    state=RetryCallState(retry,lambda:None,(),{})
    if async_mode:asyncio.run(retry._run_wait(state))
    else:retry._run_wait(state)
    assert state.upcoming_sleep==expected
