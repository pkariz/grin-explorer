from apscheduler.schedulers.background import BlockingScheduler
from django.core.management.base import BaseCommand, CommandError
from backend.api.periodic_tasks import periodically_update_blockchains_job
from backend.api.periodic_tasks import periodically_update_price_job
from backend.api.periodic_tasks import periodically_update_graphs_job
from pytz import UTC


class Command(BaseCommand):
    help = 'Run periodic tasks'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Preparing scheduler'))
        scheduler = BlockingScheduler(timezone=UTC)
        scheduler.add_job(
            periodically_update_blockchains_job, 'interval', minutes=1)
        scheduler.add_job(periodically_update_price_job, 'interval', minutes=1)
        scheduler.add_job(periodically_update_graphs_job, 'interval', minutes=5)
        self.stdout.write(self.style.NOTICE('Start scheduler'))
        scheduler.start()

