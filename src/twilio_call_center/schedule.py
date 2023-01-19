import logging

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from twilio.base.exceptions import TwilioRestException

from .models import Voicemail
from .utils import twilio_client


logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduler.start()


class VoicemailChecker:
    job_id = 'voicemail_check'
    not_found_code = 20404

    def __init__(self, interval):
        self.interval = interval
        self.interval_diff = timedelta(days=interval)
        self.initial_check_complete = False

    @classmethod
    def begin(cls):
        voicemail_lifespan = getattr(
                settings, 'TWILIO_CALL_CENTER_VOICEMAIL_LIFESPAN', None)

        if voicemail_lifespan is None:
            return
        if voicemail_lifespan <= 0:
            raise ImproperlyConfigured(
                    "TWILIO_CALL_CENTER_VOICEMAIL_LIFESPAN must be integer greater than 0")

        checker = cls(voicemail_lifespan)
        scheduler.add_job(checker.run, 'interval', replace_existing=True,
                          hours=1, id=cls.job_id)

    def run(self):
        if not self.initial_check_complete:
            self.initial_check_complete = True
            scheduler.reschedule_job(self.job_id, trigger='interval', days=1)

        for voicemail in Voicemail.objects.filter(removed_from_twilio=False):
            voicemail_expires = voicemail.last_activity + self.interval_diff
            if timezone.now() >= voicemail_expires:
                deleted = False
                try:
                    twilio_client.recordings(voicemail.sid).delete()
                    deleted = True
                except TwilioRestException as e:
                    if e.code == self.not_found_code:
                        deleted = True
                    else:
                        logger.error("Failed deleting recording " +
                                     voicemail.sid)
                        logger.error(str(e))

                if deleted:
                    voicemail.removed_from_twilio = True
                    voicemail.save()


def one_time_startup():
    VoicemailChecker.begin()
