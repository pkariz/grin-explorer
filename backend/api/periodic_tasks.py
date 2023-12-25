from .tasks import update_blockchains_progress_task
from .tasks import update_price_task
from .tasks import update_graphs


def periodically_update_blockchains_job():
    """This is ran by APScheduler."""
    update_blockchains_progress_task.send()


def periodically_update_price_job():
    """This is ran by APScheduler."""
    update_price_task.send()


def periodically_update_graphs_job():
    """This is ran by APScheduler."""
    update_graphs.send()
