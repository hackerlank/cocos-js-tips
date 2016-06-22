from django.http import HttpResponse

def get_response(content='', mimetype=None, status=None, content_type=None):
    return HttpResponse(content, mimetype, status, content_type)
    