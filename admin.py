from django.contrib import admin
from django.db import models
from django.conf.urls.defaults import patterns
from django.core.cache import cache
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404


class RedisAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(RedisAdmin, self).get_urls()

        my_urls = patterns('',
            (r'^$', self.index),
            (r'^(?P<key>.+)/delete/$', self.delete),
            (r'^(?P<key>.+)/$', self.key),
        )
        return my_urls + urls

    def index(self, request):

        if request.method == 'POST' and request.POST.getlist('_selected_action') and \
            request.POST.get('action') == 'delete_selected':

            cache.delete_many(request.POST.getlist('_selected_action'))

        if request.GET.get('q'):
            keys_result = cache._client.keys('*%s*' % request.GET.get('q'))
        else:
            keys_result = cache._client.keys('*')

        return render_to_response('redis_admin/index.html', {'keys': keys_result}, context_instance=RequestContext(request))

    def key(self, request, key):

        key_type = cache._client.type(key)
        print key_type
        
        if key_type == 'none':
            raise Http404

        context = {'key': key, 'type': key_type}

        if key_type == 'string':
             context['value'] = cache._client.get(key)
        elif key_type == 'set':
            context['value'] = str(cache._client.smembers(key))

        return render_to_response('redis_admin/key.html', context, context_instance=RequestContext(request))

    def delete(self, request, key):
        cache._client.delete(key)
        return HttpResponseRedirect('%sredis/manage/' % reverse('admin:index'))


class Meta:
    app_label = 'redis'
    verbose_name = 'Manage'
    verbose_name_plural = "Manage"

admin.site.register(type('manage', (models.Model,), {'__module__': '', 'Meta': Meta}), RedisAdmin)
