from django.test import TestCase
from twilio_call_center.models import MailboxNumber

class MailboxTestCase(TestCase):
    def setUp(self):
        MailboxNumber.objects.create(name='mailbox1',
                                     phone=None,
                                     always_send_voicemail=False)
        MailboxNumber.objects.create(name='mailbox2',
                                     phone='720-201-0123',
                                     always_send_voicemail=True)
        MailboxNumber.objects.create(name='paul',
                                     phone='720-201-0123',
                                     always_send_voicemail=False)

    def test_always_send_to_voicemail1(self):
        mailbox1 = MailboxNumber.objects.get(name='mailbox1')
        self.assertTrue(mailbox1.should_send_voicemail())

    def test_always_send_to_voicemail2(self):
        mailbox2 = MailboxNumber.objects.get(name='mailbox2')
        self.assertTrue(mailbox2.should_send_voicemail())

    def test_not_always_send_to_paul_voicemail(self):
        paul = MailboxNumber.objects.get(name='paul')
        self.assertFalse(paul.should_send_voicemail())
