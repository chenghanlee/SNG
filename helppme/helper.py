from flask import abort
from flask.ext.login import current_user
from helppme.globals import app, cache_timeout, r, CustomObjectEncoder, \
                            date_ranges, set_of_deal_list_keys
from helppme.models.deal import Deal
import simplejson as json


def get_current_user():
    '''
    This function returns the the logged in user
    '''

    #if user is not anonymous, return current user object
    if not current_user.is_anonymous():
        return current_user._get_current_object()
    else:
        return None


def debug():
    '''
    This functions allows us to explicitly break into the flask debugger
    '''
    assert app.debug == False


def is_url(some_string):
    '''
    This function looks at a string and determines is the string represents
    an url. The url must contain http://.
    '''
    from urlparse import urlparse

    # heuristic hack to check if some string is a url
    parts = urlparse(some_string)
    if not all([parts.scheme, parts.netloc]):
        return False
    elif not parts.scheme in ['http', 'https']:
        if "www." in some_string or ".com" in some_string:
            return True
        else:
            return False
    else:
        return True


'''
The following are functions are used to interact with redis
'''


def gen_key_fieldset(deal_sequence_num, prefix):
    #divider is used as the hash and remainder is used as the fieldset
    divider, remainder = divmod(deal_sequence_num, 1000)
    key = [prefix, ":", str(divider)]
    key = ''.join(key)
    return (key, remainder)


def get_deal(deal_sequence_num):
    '''
    This function takes in a deal_id and returns the associating deal object.

    We 1st checks redis to for the deal obj. If not its not found in redis,
    we retrieve the deal obj from mongohq and store the deal obj in redis
    '''
    if deal_sequence_num.__class__.__name__ == 'str':
        deal_sequence_num = int(deal_sequence_num, 10)

    #check to see if this deal is stored in the local redis cache
    key, fieldset = gen_key_fieldset(deal_sequence_num, 'deal')
    deal_json = r.hget(key, fieldset)
    if deal_json:
        return json.loads(deal_json)

    #not found in redis, retrieve it from mongodb via mongohq
    deal = Deal.objects(sequence_num=deal_sequence_num).first()
    if deal is None:
        abort(404)

    deal_json = store_deal(deal, key=key, fieldset=fieldset, return_json=True)
    return deal_json


def insert_new_deal_into_list(category,  deal_seq_num):
    '''
    This methods prepends a deal into the head (i.e. 0th element) of the lists
    that represents category

    This can be useful in circumstances where we need to preprend a new deal
    to deals lists, e.g. a user has submitted a new deal and we to reflect
    that deal in the some category's newest submitted deal list.
    '''
    for date in date_ranges:
        key = "".join([category, '_', date, '_', "newest"])
        r.lpushx(key, deal_seq_num)


def remove_deal(deal_sequence_num):
    '''
    This deal removes a deal from redis. This is used to clear staled data
    from redis and force us to reload the latest data from mongodb
    '''
    key, fieldset = gen_key_fieldset(deal_sequence_num, 'deal')
    r.hdel(key, fieldset)


def remove_deal_num_from_lists(deal_sequence_num):
    '''
    Removing deal_sequence_num from any list of deal_sequence_nums that contains
    the specific deal_sequence_num that's passed into this function.

    This is called when a user deletes a deal that he or she has authored.
    '''
    pipe = r.pipeline()
    keys = r.lrange(set_of_deal_list_keys, 0, -1)
    for key in keys:
        nums = pipe.lrange(key, 0, -1)
        if str(deal_sequence_num) in nums:
            pipe.lrem(key, 1, deal_sequence_num)
    pipe.execute()


def set_user_action_as_completed(action, deal_id, user_seq_num):
    '''
    This function denotes the user as having completed either "like", "flag",
    or "bookmarked" action.
    '''
    key = gen_user_action_hash_key(action, deal_id)
    r.setbit(key, user_seq_num, 1)


def store_deal(deal, key=None, fieldset=None, return_json=False, overwrite=False):
    '''
    Stores a deal object's json into redis
    '''
    if key is None or fieldset is None:
        key, fieldset = gen_key_fieldset(deal.sequence_num, 'deal')

    if not r.hexists(key, fieldset) or overwrite:
        deal_json = CustomObjectEncoder().encode(deal)
        r.hset(key, fieldset, deal_json)
        if return_json:  # if user requests to return the stored json
            return json.loads(deal_json)


def store_list_of_deals(key, deal_seq_nums):
    '''
    Storing a list of deals that correpsonds to a deal query into redis.
    This is used to reduce the need to query mongodb for a list of deals
    that correponds to that query e.g. "get all deals in electronics less
    than 1 wk old and sortd by popularity".

    However, race condition may occur. Therefore, we use pipe.watch and
    pipe.multi to ensure all redis transaction occur atomically. Also, if race
    conditions occur, we will retry up to 25 times. It is ok if we quit after
    25 tries because we will fallback to querying mongohq or whatever datastore
    instead. It will be slower, but we will return the correct result.
    '''
    if len(deal_seq_nums) == 0:
        # storing a -1 to denote that there are no deals associated with this key
        pipe = r.pipeline()
        pipe.rpush(key, 'None')
        pipe.expire(key, cache_timeout)
        pipe.execute()
    else:
        # creating a lock to prevent multiple threads from updating the same
        # key. In other words, we use setnx as a lock to prevent
        # race conditions between threads on updating the same key
        #
        # Also, we set the lock to expire in 10 seconds so if the lock
        # owner dies prior to releasing the lock, the lock will be released
        # automatically by redis
        #
        # Note to self:
        # It is possible that a thread has acquired a lock but the thread
        # dies before assigning an expiration to the lock or releases the lock.
        #
        # If that's the case, use the code below to ensure that we atomically
        # grab the lock and set the lock with an expiration. Because of
        # performance issues and potentially buggy code, the following piece
        # of code is not used
        #
        # lock_obtained = False
        # retries = 10
        # done = False
        # with r.pipeline() as pipe:
        #     while retries > 0 and not done:
        #         try:
        #             retries = retries - 1
        #             pipe.watch('lock')
        #             pipe.multi()
        #             pipe.setnx('lock', obtained)
        #             pipe.expires('lock', 10)
        #             lock_obtained = all(pipe.execute())
        #             done = True
        #         except WatchError
        #             continue

        lock_expiration = 3  # 3 minutes
        if r.setnx('lock', 'obtained'):  # attemp to obtain lock
            r.expire('lock', lock_expiration)
            pipe = r.pipeline()
            for num in deal_seq_nums:
                pipe.rpush(key, num)
            pipe.expire(key, cache_timeout)
            pipe.rpush(set_of_deal_list_keys, key)
            pipe.execute()
            r.delete('lock')  # release lock


def user_has(action, deal_id):
    '''
    This function is used to see if user has either flagged, saved,
    or voted a specific deal, which is denoted by deal_id

    The function returns true if a user has flagged, saved, or voted on a
    specific deal. The function returns false if otherwise.
    '''

    if action not in ['flag', 'save', 'vote']:
        return abort(404)
    user = get_current_user()
    if user is None:
        return False

    key = gen_user_action_hash_key(action, deal_id)
    user_sequence_num = user.sequence_num
    finished_action = r.getbit(key, user_sequence_num)
    if finished_action:
        return True
    else:
        # If the user action bit is false, we can't be 100% sure that
        # the user has NOT done this action. For example, the redis instance
        # may have went down, and its cache was wiped completely (or wiped
        # under other unseen circumstances).
        #
        # Therefore, if the action bit is set to false, we will query our
        # mongodb db and see if the user has accomplished any of these actions
        action_completed = False
        if action == 'flag':
            action_completed = str(deal_id) in user.deals_flagged
        elif action == 'save':
            action_completed = str(deal_id) in user.deals_saved
        elif action == "vote":
            action_completed = str(deal_id) in user.deals_voted

        if action_completed:
            r.setbit(key, user_sequence_num, 1)
        return action_completed


def gen_user_action_hash_key(action, deal_id):
    key = "".join([action, "_", str(deal_id)])
    return key
