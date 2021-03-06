#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import urllib
import logging
import json
import unicodedata
import jinja2
import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
#from google.appengine.ext import vendor needs if add apis

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GUESTBOOK_NAME = 'default_username'

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.
    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)

class Person(ndb.Model):
    """Sub model for representing a person"""
    identity = ndb.StringProperty()
    email = ndb.StringProperty()
    name = ndb.StringProperty(required=True)
    userID = ndb.StringProperty(required=True)
    year = ndb.StringProperty()
    bio = ndb.TextProperty()

class Search(ndb.Model):
    q = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

# reference link: https://cloud.google.com/appengine/docs/python/ndb/properties
class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    person = ndb.StructuredProperty(Person)
    name = ndb.StringProperty(indexed=False)
    time = ndb.StringProperty(indexed=False)
    place = ndb.StringProperty(indexed=False)
    rec = ndb.StringProperty(indexed=False)
    other = ndb.StringProperty(indexed=False)
    group1 = ndb.IntegerProperty(indexed=False)
    group2 = ndb.IntegerProperty(indexed=False)
    group3 = ndb.IntegerProperty(indexed=False)
    group4 = ndb.IntegerProperty(indexed=False) #maybe change it to boolean later
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template= JINJA_ENVIRONMENT.get_template('templates/sign_in.html')
        self.response.write(template.render({'user': user,
                                             'logout_link': users.create_logout_url('/'),
                                             'nickname': "DEFAULT" if not user else user.nickname(),
                                             'login_link': users.create_login_url('/')}))
        people = Person.query()
        if user:
            for person in people:
                if person.userID == user.user_id():
                    self.redirect('/home')
                    return
        if user:
            self.redirect('/create_profile')

# making a login page integrated with Google accounts.
# user must log in to view contents.

class MainPage(webapp2.RequestHandler):

    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            self.redirect(users.create_login_url(self.request.uri))

        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
        }

        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.write(template.render(template_values))

class CreateProfileHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template = JINJA_ENVIRONMENT.get_template('templates/profile_form.html')
        self.response.write(template.render({'user': user,
                                             'logout_link': users.create_logout_url('/'),
                                             'nickname': "DEFAULT" if not user else user.nickname(),
                                             'login_link': users.create_login_url('/')}))
    def post(self):
        user = users.get_current_user()
        person = Person(
            name=self.request.get('name'),
            identity=user.user_id(),
            userID=user.user_id(),
            email=user.email(),
            year=self.request.get('year'),
            bio=self.request.get('bio'))
        person.put()
        self.redirect('/home')

class Guestbook(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.person = Person(
                    identity=users.get_current_user().user_id(),
                    userID=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.name = self.request.get('name')
        greeting.time = self.request.get('time')
        greeting.place = self.request.get('place')
        greeting.rec = self.request.get('rec')
        greeting.other = self.request.get('other')
        greeting.group1 = int(self.request.get('group1'))
        greeting.group2 = int(self.request.get('group2'))
        greeting.group3 = int(self.request.get('group3')) #maybe change it to boolean later
        greeting.group4 = int(self.request.get('group4'))
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

class ProfileHandler(webapp2.RequestHandler):
    def get(self):
        people = Person.query()

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            self.redirect(users.create_login_url(self.request.uri))

        template_values = {
            'user': user,
            'people': people,
        }
        template= JINJA_ENVIRONMENT.get_template('templates/my_profile.html')
        self.response.write(template.render(template_values))

class SearchFormHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template = JINJA_ENVIRONMENT.get_template('templates/search_input.html')
        self.response.write(template.render({'user': user,
                                             'logout_link': users.create_logout_url('/'),
                                             'nickname': "DEFAULT" if not user else user.nickname(),
                                             'login_link': users.create_login_url('/')}))

    def post(self):
        user = users.get_current_user()
        search = Search(
            q=self.request.get('q'))
        search.put()
        self.redirect('/search')


class AboutPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if users.get_current_user():
            template_values = {
                'user': user
            }
            template= JINJA_ENVIRONMENT.get_template('templates/about.html')
            self.response.write(template.render(template_values))

class RecentPage(webapp2.RequestHandler):
    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(100)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            self.redirect(users.create_login_url(self.request.uri))

        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
        }
        template= JINJA_ENVIRONMENT.get_template('templates/recent.html')
        self.response.write(template.render(template_values))

class SearchPage(webapp2.RequestHandler):
    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(100)

        search = Search.query().order(-Search.date).fetch(1)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            self.redirect(users.create_login_url(self.request.uri))

        template_values = {
            'user': user,
            'search': search,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
        }
        template= JINJA_ENVIRONMENT.get_template('templates/search.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/create_profile', CreateProfileHandler),
    ('/club', MainPage),
    ('/sign', Guestbook),
    ('/about', AboutPage),
    ('/home', SearchFormHandler),
    ('/profile', ProfileHandler),
    ('/search', SearchPage),
    ('/recent', RecentPage)
], debug=True)
