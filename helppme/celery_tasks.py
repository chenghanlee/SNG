from helppme.globals import task_retry_delay
from helppme.models.user import User
from helppme.models.deal import Deal
from helppme.models.vote import Vote

from celery.task import task


@task(name='celery_tasks.delete', ignore_result=True)
def delete(deal_id):
    try:
        deal = Deal.objects(id=deal_id).first()
        deal.deleted = True
        deal.save()
    except Exception, exc:
        #log error here
        delete.retry(exc=exc, countdown=task_retry_delay)


@task(name='celery_tasks.flag', ignore_result=True)
def flag(deal_id, user_id):
    try:
        deal_queryset = Deal.objects(id=deal_id)
        deal_queryset.update_one(push__flags=user_id)
    except Exception, exc:
        #log error here
        flag.retry(exc=exc, delay=task_retry_delay)


@task(name='celery_tasks.send_email', ignore_result=True)
def send_email(sender, recipients, title, body, bcc=None):
    try:
        message = Message(subject=title,
                          sender=sender,
                          body=body,
                          recipients=recipients,
                          bcc=bcc)

        mail.connect()
        mail.send(message)
    except Exception, exc:
        upvote.retry(exc=exc, delay=task_retry_delay)


@task(name='celery_tasks.upvote', ignore_result=True)
def upvote(deal_id, user_id, remote_addr):
    try:
        new_vote = Vote(deal_id=str(deal_id), ip=remote_addr,
                        voter_id=str(user_id))
        new_vote.save()
        Deal.objects(id=deal_id).update_one(push__votes=str(new_vote.id))
        user = User.objects(id=user_id).first()
        user.votes.append(str(new_vote.id))
        user.save()
    except Exception, exc:
        #log error here
        upvote.retry(exc=exc, delay=task_retry_delay)
