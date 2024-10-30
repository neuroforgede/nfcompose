import uuid
from psycopg import errors  # type: ignore
from typing import Dict, Callable, Union
from skipper.core.celery import task
from skipper.dataseries.models.task_data import MetaModelTaskData
from django.db import transaction
from celery.utils.log import get_task_logger  # type: ignore
from django_multitenant.utils import set_current_tenant  # type: ignore


logger = get_task_logger(__name__)

meta_model_task_registry: Dict[str, Callable[[MetaModelTaskData], None]]= {}


def spawn_meta_model_task(task_data_id: Union[uuid.UUID, str]) -> None:
    run_meta_model_task.delay(task_data_id)


@task(name="_3_dynamic_sql_run_meta_model_task",
      autoretry_for=(errors.DeadlockDetected,),  # type: ignore
      retry_backoff=True,  # type: ignore
      retry_kwargs={'max_retries': None, 'countdown': 5})  # type: ignore
def run_meta_model_task(
    meta_model_task_data_id: str
) -> None:
    with transaction.atomic():
        # this must run outside of any tenant context or we dont get all data in a multitenant environment
        set_current_tenant(None)
        # skip the task if it was already claimed by another task
        task_data: MetaModelTaskData = MetaModelTaskData.objects.filter(
            id=meta_model_task_data_id
        ).select_for_update(skip_locked=True).first()
        if task_data is None:
            logger.warn('task data not found, either claimed by someone else or task does not exist (anymore)')
        if task_data is not None:
            _func = meta_model_task_registry.get(task_data.task, None)
            if _func is None:
                logger.warn(f'task function {task_data.name} not found.')
                return
            
            _func(task_data)

            task_data.delete()