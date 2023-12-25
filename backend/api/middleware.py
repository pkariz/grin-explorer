from dramatiq.middleware import Middleware, CurrentMessage
from dramatiq_abort.abort_manager import Abort as AbortException


class UpdateDramatiqTaskMiddleware(Middleware):
    """Updates DramatiqTask instance when the task is done."""

    def after_process_message(
        self, broker, message, *, result=None, exception=None
    ):
        # import here because at the top apps are not yet loaded
        from .models import DramatiqTask
        task = DramatiqTask.objects\
            .filter(message_id=message.message_id)\
            .first()
        if task:
            if task.type == DramatiqTask.Type.BLOCKCHAIN_DELETE:
                task.delete()
                return
            status = DramatiqTask.Status.SUCCESS
            failure_reason = None
            if exception:
                status = DramatiqTask.Status.FAILURE
                failure_reason = str(exception)
                if isinstance(exception, AbortException):
                    failure_reason = 'Aborted'
            task.status = status
            task.failure_reason = failure_reason
            task.save()

    def after_skip_message(self, broker, message):
        # import here because at the top apps are not yet loaded
        from .models import DramatiqTask
        task = DramatiqTask.objects\
            .filter(message_id=message.message_id)\
            .first()
        if task:
            task.status = DramatiqTask.Status.SKIPPED
            task.save()

    def after_worker_shutdown(self, broker, worker):
        # import here because at the top apps are not yet loaded
        from .models import DramatiqTask
        message = CurrentMessage.get_current_message()
        task = DramatiqTask.objects\
            .filter(message_id=message.message_id)\
            .first()
        if task and task.status == DramatiqTask.Status.IN_PROGRESS:
            task.status = DramatiqTask.Status.FAILURE
            task.failure_reason = 'Worker shutdown'
            task.save()

