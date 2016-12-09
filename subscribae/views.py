from django.http import HttpResponse


def home(request):
    return HttpResponse("Hello")


def bucket(request, bucket):
    return HttpResponse("Hello %s" % bucket)


def subscription(request, subscription):
    return HttpResponse("Hello %s" % subscription)


def video(request, video):
    return HttpResponse("Hello %s" % video)
