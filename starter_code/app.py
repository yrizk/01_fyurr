#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'venue'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String())
  genres = db.Column(db.String(120))
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(20))
  website = db.Column(db.String(500))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean)
  seeking_description = db.Column(db.String(500))

  def __repr__(self):
      return f'{self.id},{self.name},{self.genres},{self.city},{self.state},{self.phone},{self.website},{self.address},{self.phone},{self.image_link},{self.facebook_link},{self.seeking_talent},{self.seeking_description},{self.shows}'

class Artist(db.Model):
  __tablename__ = 'artist'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  genres = db.Column(db.String(120))
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean)
  seeking_description = db.Column(db.String(500))

  def __repr__(self):
      return f'<Artist id={self.id},name={self.name},genres={self.genres},city={self.city},state={self.state},phone={self.phone},image_link={self.image_link},facebook_link={self.facebook_link},seeking_venue={self.seeking_venue},seeking_description={self.seeking_description},shows={self.shows}>'

class Show(db.Model):
  __tablename__ = 'show'
  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
  start_time = db.Column(db.String(), nullable=False, default=datetime.utcnow())
  venue = db.relationship('Venue', backref=db.backref('shows', lazy=True))
  artist = db.relationship('Artist', backref=db.backref('shows', lazy=True))

  def __repr__(self):
      return f'<Show id={self.id},artist_id={self.artist_id},venue_id={self.venue_id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(str(value))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  distinct_city_state_tuple = db.session.query(Venue.city, Venue.state).distinct().all()
  data = []
  for city, state in distinct_city_state_tuple:
      obj = {}
      obj['city'] = city
      obj['state'] = state
      obj['venues'] = []
      vs = Venue.query.filter_by(city=city).filter_by(state=state).with_entities(Venue.id, Venue.name).all()
      for v1 in vs:
        v = {}
        v['id'] = v1.id
        v['name'] = v1.name
        _ , v['num_upcoming_shows'] = split_shows(Venue.query.get(v1.id))
        obj['venues'].append(v)
      data.append(obj)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  query_results = Venue.query.filter(func.lower(Venue.name).contains(request.form.get('search_term', '').lower(), autoescape=True)).with_entities(Venue.id, Venue.name)
  data = {}
  data['count'] = query_results.count()
  data['data'] = []
  for q in query_results.all():
      sub_result = {}
      sub_result['id'] = q.id
      sub_result['name'] = q.name
      _ , sub_result['num_upcoming_shows'] = split_shows(Venue.query.get(q.id))
      data['data'].append(sub_result)
  return render_template('pages/search_venues.html', results=data, search_term=request.form.get('search_term', ''))

# splits the shows attribute into num_past_shows, num_upcoming_shows
# applies to venues or artists
def split_shows(va):
    num_past_shows = 0
    num_upcoming_shows = 0
    for show in va.shows:
        if datetime.now() >= show.start_time:
            num_past_shows += 1
        else:
            num_upcoming_shows +=1
    return num_past_shows, num_upcoming_shows

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    venue.genres = venue.genres.split(",")
    venue.past_shows_count, venue.upcoming_shows_count = split_shows(venue)
    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  new_info = request.form
  error = False
  try:
    v = Venue()
    v.name = new_info['name']
    v.city = new_info['city']
    v.state = new_info['state']
    v.phone = new_info['phone']
    v.genres = ','.join(new_info['genres'])
    v.facebook_link = new_info['facebook_link']
    db.session.add(v)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  venue_id = request.form.get('venue_id', '')
  try:
    Todo.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({ 'success': True })

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.order_by('id').with_entities(Artist.id, Artist.name).all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  query_results = Artist.query.filter(func.lower(Artist.name).contains(request.form.get('search_term', '').lower(), autoescape=True)).with_entities(Artist.id, Artist.name)
  response = {}
  response['count'] = query_results.count()
  response['data'] = []
  for a in query_results.all():
    r = {}
    r['id'] = a.id
    r['name'] = a.name
    r['num_upcoming_shows'] = split_shows(Artist.query.get(a.id))
    response['data'].append(r)
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  artist.genres = artist.genres.split(",")
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  return render_template('forms/edit_artist.html', form=form, artist=Artist.query.get(artist_id))

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  print(request.form)
  new_info = request.form
  a = Artist.query.get(artist_id)
  a.name = new_info['name']
  a.city = new_info['city']
  a.state = new_info['state']
  a.phone = new_info['phone']
  a.genres = ','.join(new_info['genres'])
  a.facebook_link = new_info['facebook_link']
  db.session.commit()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  return render_template('forms/edit_venue.html', form=form, venue=Venue.query.get(venue_id))

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  new_info = request.form
  v = Venue.query.get(venue_id)
  v.name = new_info['name']
  v.city = new_info['city']
  v.state = new_info['state']
  v.address = new_info['address']
  v.phone = new_info['phone']
  v.genres = ','.join(new_info['genres'])
  v.facebook_link = new_info['facebook_link']
  db.session.commit()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  new_info = request.form
  error = False
  try:
    a = Artist()
    a.name = new_info['name']
    a.city = new_info['city']
    a.state = new_info['state']
    a.phone = new_info['phone']
    a.genres = ','.join(new_info['genres'])
    a.facebook_link = new_info['facebook_link']
    db.session.add(a)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  results = []
  for show in Show.order_by('id').query.all():
      obj = {}
      venue = Venue.query.get(show.venue_id)
      artist = Artist.query.get(show.artist_id)
      obj['venue_id'] = venue.id
      obj['venue_name'] = venue.name
      obj['artist_id'] = artist.id
      obj['artist_name'] = artist.name
      obj['artist_image_link'] = artist.image_link
      obj['start_time'] = str(show.start_time)
      results.append(obj)
  return render_template('pages/shows.html', shows=results)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    new_info = request.form
    s = Show()
    s.artist_id = new_info['artist_id']
    s.venue_id = new_info['venue_id']
    db.session.add(s)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('Show was not created. Make sure the artist and the venue exist')
  else:
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
