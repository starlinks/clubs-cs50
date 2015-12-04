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
        person = Person(name = self.request.get('name'),
                        userID = user.user_id(),
                        email = user.email(),
                        year = self.request.get('year'),
                        bio = self.request.get('bio'))
        person.put()
        self.redirect('/home')
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
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
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
        '''user = users.get_current_user()
        person = Person(name = self.request.get('person_name'),
                        userID = user.user_id(),
                        email = user.email(),
                        year = self.request.get('year'),
                        bio = self.request.get('bio'))
        person.put()
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))'''

        user= users.get_current_user
        person = Person(
            name=self.request.get('name'),
            identity=users.get_current_user().user_id(),
            userID=users.get_current_user().user_id(),
            email=users.get_current_user().email(),
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

        '''if users.get_current_user():
            greeting.person = Person(
                    identity=users.get_current_user().user_id(),
                    userID=users.get_current_user().user_id(),
                    email=users.get_current_user().email()'''

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

        '''query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))''' #why doesn't this work? It notes the identity
        self.redirect('/home')

class PersonClub(ndb.Model):
    person = ndb.KeyProperty(Person)
    greeting = ndb.KeyProperty(Greeting)

class ProfileHandler(webapp2.RequestHandler):
    def get(self):
        '''guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)'''
        #the above is not needed until club entries are added in
        user = users.get_current_user()
        template_values = {'user': user,
                           'logout_link': users.create_logout_url('/'),
                           'nickname': "DEFAULT" if not user else user.nickname(),
                           'login_link': users.create_login_url('/')}
        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/my_profile.html')
            current_id = self.request.get('id')
            people = Person.query()
            # logging.info(people)
            for person in people:
                if person.userID == user.user_id():
                    template_values['name'] = person.name
                    template_values['year'] = person.year
                    template_values['email'] = person.email
                    template_values['bio'] = person.bio
                    break
            if current_id != "":
                person_key = None

                for person in people:
                    logging.info(person.userID)
                    logging.info(current_id)
                    if person.userID == current_id:
                        logging.info("==============heyo it's a match")
                        person_key = person.key
                        break
                if person_key:
                    person = person_key.get()
                    template_values['name'] = person.name
                    template_values['email'] = person.email    #user.email()
                    template_values['year'] = person.year
                    template_values['bio'] = person.bio

        # template = JINJA_ENVIRONMENT.get_template('templates/my_profile.html')
        evaluations = PersonClub.query().fetch()
        template_values['results'] = ""
        for evaluation in evaluations:
            if evaluation and evaluation.person and evaluation.person.get():
                logging.info(evaluation.person.get().name)
                logging.info(template_values['name'])
            if evaluation and evaluation.person and evaluation.person.get():
                if evaluation.person.get().name == template_values['name']:
                    greeting = evluation.greeting.get()
                    greeting_id = str(greeting.key.id())

                    template_values['results'] += greeting.name
        self.response.write(template.render(template_values))


class AboutPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if users.get_current_user():
            template_values = {
                'user': user
            }
            template= JINJA_ENVIRONMENT.get_template('templates/about.html')
            self.response.write(template.render(template_values))

# https://cloud.google.com/appengine/docs/python/search/faceted_search
"""class IndexPage(webapp2.RequestHandler):
    '''def put(self):
        doc = search.Document(doc_id='doc1', fields=[search.AtomField(name='name', value='x86')],
            facets = [search.AtomFacet(name='type', value='CS50')])
        index = search.Greeting(name='products', namespace='')
        index.put(doc)'''
    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting1 = Greeting(parent=guestbook_key(guestbook_name)
        Greeting.query(ancestor=guestbook_key(guestbook_name)).fetch()

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
        }
        template= JINJA_ENVIRONMENT.get_template('templates/search.html')
        self.response.write(template.render(template_values))
"""

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
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
        }
        template= JINJA_ENVIRONMENT.get_template('templates/recent.html')
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/create_profile', CreateProfileHandler),
    ('/home', MainPage),
    ('/about', AboutPage),
    ('/profile', ProfileHandler),
    ('/recent', RecentPage)
], debug=True)
