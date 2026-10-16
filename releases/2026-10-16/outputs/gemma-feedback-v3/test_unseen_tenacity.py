"""Controls withheld from the feedback prompt; authored before reading response."""
import asyncio
import pytest
from tenacity import Retrying,AsyncRetrying,RetryCallState

class DynamicFalse:
    def __bool__(self):return False
    def __call__(self,state):return state.attempt_number+.5

class EmptyDynamic(list):
    def __call__(self,state):return state.attempt_number+.75

class AsyncFalse:
    def __bool__(self):return False
    async def __call__(self,state):return state.attempt_number+.25

@pytest.mark.parametrize('strategy,expected',[(DynamicFalse(),2.5),(EmptyDynamic(),2.75),(None,0),(0.0,0)])
@pytest.mark.parametrize('async_mode',[False,True])
def test_unseen_wait(strategy,expected,async_mode):
    retry=(AsyncRetrying if async_mode else Retrying)(wait=strategy)
    state=RetryCallState(retry,lambda:None,(),{});state.attempt_number=2
    if async_mode:asyncio.run(retry._run_wait(state))
    else:retry._run_wait(state)
    assert state.upcoming_sleep==expected

def test_false_async_callable():
    retry=AsyncRetrying(wait=AsyncFalse());state=RetryCallState(retry,lambda:None,(),{});state.attempt_number=2
    asyncio.run(retry._run_wait(state));assert state.upcoming_sleep==2.25
