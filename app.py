#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_wtf import FlaskForm as Form
from flask_migrate import Migrate
from datetime import datetime
import sys
from flask_sqlalchemy import SQLAlchemy

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
from models import *
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  event_venue = Venue.query.order_by('id').all()
  data = []

  for venue in event_venue:
    data += [{
      "city": venue.city,
      "state": venue.state,
      "venues":[{
        "id": venue.id,
        "name": venue.name,
      }]
    }]

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_request = request.form.get('search_term', '')
  word = format(search_request.lower())
  search_query = '%{}%'.format(word)

  by_name = Venue.name.ilike(search_query)
  by_city = Venue.city.ilike(search_query)
  by_state = Venue.state.ilike(search_query)

  results = Venue.query.filter(by_name | by_city | by_state).all()

  response = {
    'count':len(results),
    'data': results
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue_info = Venue.query.filter_by(id=venue_id).first()

  _id = venue_info.id
  _name = venue_info.name
  _genres = venue_info.genres.split(", ")
  _address = venue_info.address
  _city = venue_info.city
  _state = venue_info.state
  _phone = venue_info.phone
  _website = venue_info.website
  _facebook_link = venue_info.facebook_link
  _seeking_talent = venue_info.seeking_talent
  _seeking_description = venue_info.seeking_description
  _image_link = venue_info.image_link
  _upcoming_shows = []
  _past_shows = []

  past_data = db.session.query(Show.start_time, Artist.id, Artist.name, Artist.image_link).join(Venue, Artist).filter(Show.start_time < datetime.today(), Show.venue_id==venue_info.id).all()
  upcoming_data = db.session.query(Show.start_time, Artist.id, Artist.name, Artist.image_link).join(Venue, Artist).filter(Show.start_time > datetime.today(), Show.venue_id==venue_info.id).all()

  for start_time, artist_id, artist_name, image_link in upcoming_data:
    _upcoming_shows += [
      {
        "artist_id": artist_id,
        "artist_name": artist_name,
        "artist_image_link": image_link,
        "start_time": str(start_time)
      }
    ]

  
  for start_time, artist_id, artist_name, image_link in past_data:
    _past_shows += [
      {
        "artist_id": artist_id,
        "artist_name": artist_name,
        "artist_image_link": image_link,
        "start_time": str(start_time)
      }
    ]

  
  data={
    "id": _id,
    "name": _name,
    "genres":  _genres,
    "address": _address,
    "city": _city,
    "state": _state,
    "phone": _phone,
    "website": _website,
    "facebook_link": _facebook_link,
    "seeking_talent": _seeking_talent,
    "seeking_description":  _seeking_description,
    "image_link": _image_link,
    "past_shows": _past_shows,
    "upcoming_shows": _upcoming_shows,
    "past_shows_count": len(past_data),
    "upcoming_shows_count": len(upcoming_data),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    address = request.form.get('address')
    genres = ", ".join(request.form.getlist('genres'))
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')
    website_link = request.form.get('website_link')
    seeking_talent = request.form.get('seeking_talent', type=bool)
    seeking_description = request.form.get('seeking_description')

    venue = Venue()
    venue.name = name
    venue.city = city
    venue.state = state
    venue.phone = phone
    venue.address = address
    venue.genres = genres
    venue.facebook_link = facebook_link
    venue.image_link = image_link
    venue.website = website_link
    venue.seeking_talent = seeking_talent
    venue.seeking_description = seeking_description


    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if not error:
    flash('Venue ' + request.form.get('name') + ' was successfully listed!')
  else:
    flash('An error occurred. Venue ' + request.form.get('name') + ' could not be listed.')
    abort(500)
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    delete_venues = Venue.query.get(venue_id)
    db.session.delete(delete_venues)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  if not error:
        return render_template('pages/home.html'), 200
  else:
    abort(500)

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = db.session.query(Artist).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_request = request.form.get('search_term', '')
  word = format(search_request.lower())
  search_query = '%{}%'.format(word)

  by_name = Artist.name.ilike(search_query)
  by_city = Artist.city.ilike(search_query)
  by_state = Artist.state.ilike(search_query)

  results = Artist.query.filter(by_name | by_city | by_state).all()

  response = {
    'count':len(results),
    'data': results
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist_info = Artist.query.filter_by(id=artist_id).first()

  _id = artist_info.id
  _name = artist_info.name
  _genres = artist_info.genres.split(", ")
  _city = artist_info.city
  _state = artist_info.state
  _phone = artist_info.phone
  _website = artist_info.website
  _facebook_link = artist_info.facebook_link
  _seeking_venue = artist_info.seeking_venue
  _seeking_description = artist_info.seeking_description
  _image_link = artist_info.image_link
  _upcoming_shows = []
  _past_shows = []

  past_data = db.session.query(Show.start_time, Venue.id, Venue.name, Venue.image_link).join(Venue, Artist).filter(Show.start_time < datetime.today(),Show.artist_id==artist_info.id).all()
  upcoming_data = db.session.query(Show.start_time, Venue.id, Venue.name, Venue.image_link).join(Venue, Artist).filter(Show.start_time > datetime.today(),Show.artist_id==artist_info.id).all()
  

  for start_time, venue_id, venue_name, image_link in upcoming_data:
    _upcoming_shows += [
      {
        "venue_id": venue_id,
        "venue_name": venue_name,
        "venue_image_link": image_link,
        "start_time": str(start_time)
      }
    ]

  
  for start_time, venue_id, venue_name, image_link in past_data:
    _past_shows += [
      {
        "venue_id": venue_id,
        "venue_name": venue_name,
        "venue_image_link": image_link,
        "start_time": str(start_time)
      }
    ]
  
  data={
    "id": _id,
    "name": _name,
    "genres": _genres,
    "city": _city,
    "state": _state,
    "phone": _phone,
    "website": _website,
    "facebook_link": _facebook_link,
    "seeking_venue": _seeking_venue,
    "seeking_description": _seeking_description,
    "image_link": _image_link,
    "past_shows": _past_shows,
    "upcoming_shows": _upcoming_shows,
    "past_shows_count": len(past_data),
    "upcoming_shows_count": len(upcoming_data),
  }
  
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  try:
    artist = Artist.query.get(artist_id)
    if request.method == 'POST':
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = ", ".join(form.genres.data)
      artist.image_link = form.image_link.data
      artist.facebook_link = form.facebook_link.data
      artist.website = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data
      
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.genres.data = venue.genres
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.website_link.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  form = VenueForm(request.form)
  try:
    venue = Venue.query.get(venue_id)
    if request.method == 'POST':
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = ", ".join(form.genres.data)
      venue.image_link = form.image_link.data
      venue.facebook_link = form.facebook_link.data
      venue.website = form.website_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      
      db.session.add(venue)
      db.session.commit()
      flash('venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  error = False
  try:  
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = ", ".join(request.form.getlist('genres'))
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')
    website_link = request.form.get('website_link')
    seeking_venue = request.form.get('seeking_venue', type=bool)
    seeking_description = request.form.get('seeking_description')

    data = Artist()
    data.name=name
    data.city=city
    data.state=state
    data.phone=phone
    data.genres=genres
    data.facebook_link=facebook_link
    data.image_link=image_link
    data.website=website_link
    data.seeking_venue= seeking_venue
    data.seeking_description=seeking_description

    db.session.add(data)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    flash('Artist ' + request.form.get('name') + ' was successfully listed!')
  else:
    flash('An error occurred. Artist ' + request.form.get('name') + ' could not be listed.')
    abort(500)
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #data = Show.query.all()
  all_shows = Show.query.order_by('id').all()
  
  data = []

  for show in all_shows:
    name = Artist.query.filter_by(id=show.artist_id).first()
    venue = Venue.query.filter_by(id=show.venue_id).first()
    data += [{
      "artist_id": name.id,
      "artist_name": name.name,
      "venue_id": venue.id,
      "venue_name": venue.name,
      "start_time": str(show.start_time)
    }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  try:
    artist = request.form.get('artist_id')
    venue = request.form.get('venue_id')
    time = request.form.get('start_time')

    data = Show()
    data.artist_id = artist
    data.venue_id = venue
    data.start_time = str(time)

    db.session.add(data)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if not error:
    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed.')
    abort(500)
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
