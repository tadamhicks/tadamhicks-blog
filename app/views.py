import datetime
import functools
import os
import re
import urllib

from flask import (Flask, flash, Markup, redirect, render_template, request,
                   Response, session, url_for)
from playhouse.flask_utils import get_object_or_404, object_list
from .models import Entry, FTSEntry
from peewee import *
from app import app, database


def login_required(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        if session.get('logged_in'):
            return fn(*args, **kwargs)
        return redirect(url_for('login', next=request.path))
    return inner


@app.route('/login/', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or request.form.get('next')
    if request.method == 'POST' and request.form.get('password'):
        password = request.form.get('password')
        # TODO: If using a one-way hash, you would also hash the user-submitted
        # password and do the comparison on the hashed versions.
        if password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            session.permanent = True  # Use cookie to store session.
            flash('You are now logged in.', 'success')
            return redirect(next_url or url_for('index'))
        else:
            flash('Incorrect password.', 'danger')
    return render_template('login.html', next_url=next_url)


@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        return redirect(url_for('login'))
    return render_template('logout.html')


@app.route('/')
def index():
    search_query = request.args.get('q')
    if search_query:
        query = Entry.search(search_query)
    else:
        query = Entry.public().order_by(Entry.timestamp.desc())

    # The `object_list` helper will take a base query and then handle
    # paginating the results if there are more than 20. For more info see
    # the docs:
    # http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#object_list
    return object_list(
        'index.html',
        query,
        search=search_query,
        check_bounds=False)


def _create_or_edit(entry, template):
    if request.method == 'POST':
        entry.title = request.form.get('title') or ''
        entry.content = request.form.get('content') or ''
        entry.published = request.form.get('published') or False
        if not (entry.title and entry.content):
            flash('Title and Content are required.', 'danger')
        else:
            # Wrap the call to save in a transaction so we can roll it back
            # cleanly in the event of an integrity error.
            try:
                with database.atomic():
                    entry.save()
            except IntegrityError:
                flash('Error: this title is already in use.', 'danger')
            else:
                flash('Entry saved successfully.', 'success')
                if entry.published:
                    return redirect(url_for('detail', slug=entry.slug))
                else:
                    return redirect(url_for('edit', slug=entry.slug))

    return render_template(template, entry=entry)


@app.route('/create/', methods=['GET', 'POST'])
@login_required
def create():
    return _create_or_edit(Entry(title='', content=''), 'create.html')


@app.route('/drafts/')
@login_required
def drafts():
    query = Entry.drafts().order_by(Entry.timestamp.desc())
    return object_list('index.html', query, check_bounds=False)


@app.route('/<slug>/')
def detail(slug):
    if session.get('logged_in'):
        query = Entry.select()
    else:
        query = Entry.public()
    entry = get_object_or_404(query, Entry.slug == slug)
    return render_template('detail.html', entry=entry)


@app.route('/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit(slug):
    entry = get_object_or_404(Entry, Entry.slug == slug)
    return _create_or_edit(entry, 'edit.html')


@app.template_filter('clean_querystring')
def clean_querystring(request_args, *keys_to_remove, **new_values):
    # We'll use this template filter in the pagination include. This filter
    # will take the current URL and allow us to preserve the arguments in the
    # querystring while replacing any that we need to overwrite. For instance
    # if your URL is /?q=search+query&page=2 and we want to preserve the search
    # term but make a link to page 3, this filter will allow us to do that.
    querystring = dict((key, value) for key, value in request_args.items())
    for key in keys_to_remove:
        querystring.pop(key, None)
    querystring.update(new_values)
    return urllib.urlencode(querystring)


@app.errorhandler(404)
def not_found(exc):
    return Response('<h3>Not found</h3>'), 404


def main():
    database.create_tables([Entry, FTSEntry], safe=True)
    app.run(debug=True)


if __name__ == '__main__':
    main()
