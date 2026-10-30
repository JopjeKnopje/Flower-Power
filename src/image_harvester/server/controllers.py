from litestar import Controller, get
from litestar.di import NamedDependency

from core.models.models import TestModel


class RootController(Controller):
    @get()
    def hello(self, test_model: NamedDependency[TestModel]) -> TestModel:

        # try:
        #     val = get_queue.get(block=False)
        # except Empty:
        #     raise HTTPException(detail="Queue empty", status_code=400)
        return test_model
