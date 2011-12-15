from helppme.globals import app, DATETIME_FORMAT
from helppme.models.deal import pretty_date
from datetime import datetime


@app.template_filter('format_location')
def format_location(location):
    '''
    This function checks location to determine if the location is an url.
    If not, the function returns "In-Store"

    If the location is an url, it strips the url to xyz.com. If the
    location is a physical store, it will add B&M to the end of location
    '''

    import string

    #not a url, assume location is a physical store
    #a url, stripping everything except for xxx.com
    if location:
        start = string.find(location, '//') + 2
        sub_url = location[start:]
        end = string.find(sub_url, '/')
        if end > -1:
            sub_url = location[start: start + end]
        sub_url = string.replace(sub_url, 'www.', '')
        return sub_url
    else:
        return "in-store"


@app.template_filter('prettify')
def prettify(date):
    '''
    This function takes a regulary python datetime object and returns
    a "prettier" verion of the datetime object in terms of x seconds ago,
    x minutes ago, x days ago, and so forth.
    '''
    orig_time = datetime.strptime(date, DATETIME_FORMAT)
    return pretty_date(orig_time)
