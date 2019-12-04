from app import app, db
from app.models import User, Genre, User_genre, Movie, Later_movie, Favorited_movie
from flask import request, make_response, jsonify
from flask_cors import CORS
import requests
import json
import random
from flask import request
import dotenv
import os
from lxml import html

CORS(app, resources={r"/*": {"origins": [os.getenv('ORIGIN')]}})

dotenv.load_dotenv()
TMDB_key = os.getenv('TMDB_KEY')

# Route for generating a movie suggestion
@app.route("/suggestion", methods=['GET', 'POST'])
def suggestions():
  req = json.loads(request.data)
  user_genre_preferences = req['userGenrePreferences']

  # Make list of previously suggested movie ids
  suggested_ids = []
  for suggestion in req['recentSuggestions']:
    suggested_ids.append(suggestion['newSuggestion']['tmdb_id'])

  # Convert user preferences to more useable object
  preferences = {}
  for user_preference in user_genre_preferences:
    preferences[user_preference['id']] = user_preference['preference']

  # Get any group preferences
  for user in req['group']:
    genre_preferences = User_genre.query.filter(User_genre.user_id == user['friend']['id']).all()

    for genre in genre_preferences:
      if preferences[genre.genre.genre_api_id] != False:
        if genre.preference == False:
          preferences[genre.genre.genre_api_id] = False
        elif genre.preference == True:
          preferences[genre.genre.genre_api_id] = True

  # Break-up all preferences into lists for each preference
  user_loved_genres = []
  user_meh_genres = []
  user_hated_genres = []

  for genre in preferences:
    if preferences[genre] == True:
      user_loved_genres.append(str(genre))
    elif preferences[genre] == "" or preferences[genre] == None:
      user_meh_genres.append(str(genre))
    elif preferences[genre] == False:
      user_hated_genres.append(str(genre))

# Check if no genres are in meh or loved, thus all are hated and we return Bob Ross movie
  if len(user_meh_genres) == 0 and len(user_loved_genres) == 0:

    if len(req['group']) == 0:
      error = "solo"
    else:
      error = "group"

    full_hate_info = {
    "error": error,
    "title": "Bob Ross: The Happy Painter",
    "poster": "https://image.tmdb.org/t/p/w500/yhV6rSv8Ry80lyDL8sjZpu8hzph.jpg",
    "description": "A behind-the-scenes look at the beloved public television personality's journey from humble beginnings to an American pop-culture icon. \"The Happy Painter\" reveals the public and private sides of Bob Ross through loving accounts from close friends and family, childhood photographs and rare archival footage.  Interviewees recount his gentle, mild-mannered demeanor and unwavering dedication to wildlife, and disclose little-known facts about his hair, his fascination with fast cars and more.  Film clips feature Bob Ross with mentor William Alexander and the rough-cut of the first \"Joy of Painting\" episode from 1982. Famous Bob Ross enthusiasts, including talk-show pioneer Phil Donahue, film stars Jane Seymour and Terrence Howard, chef Duff Goldman and country music favorites Brad Paisley and Jerrod Niemann, provide fascinating insights into the man, the artist and his legacy.",
    "release_date": "2011",
    "tmdb_id": "238959",
    "imdb_link": "https://www.imdb.com/title/tt2155259/"
    }

    full_hate_info_json = json.dumps(full_hate_info)
    return full_hate_info_json

# Make hated genre query string
  if len(user_hated_genres) > 1:
    hated_list = (",".join(user_hated_genres))
  elif len(user_hated_genres) == 1:
    hated_list = user_hated_genres[0]
  elif len(user_hated_genres) == 0:
    hated_list = "0"

  user_loved_genres_loop_copy = user_loved_genres.copy()
  user_meh_genres_loop_copy = user_meh_genres.copy()
  all_results = []

  while len(all_results) == 0:
    page_num = random.randint(1, 3)

    if len(user_loved_genres_loop_copy) != 0:
      index = random.randint(0, (len(user_loved_genres_loop_copy) - 1))
      r = requests.get("https://api.themoviedb.org/3/discover/movie?api_key={}&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page={}&with_genres={}&without_genres={}&with_runtime.gte=20&release_date.lte=2020-04-01".format(TMDB_key, page_num, user_loved_genres_loop_copy[index], hated_list))
      this_one = ["PAGE", page_num, "INDEX", index, "A LOVED"]
      del user_loved_genres_loop_copy[index]
    elif len(user_meh_genres_loop_copy) != 0:
      index = random.randint(0, (len(user_meh_genres_loop_copy) - 1))
      r = requests.get("https://api.themoviedb.org/3/discover/movie?api_key={}&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page={}&with_genres={}&without_genres={}&with_runtime.gte=20&release_date.lte=2020-04-01".format(TMDB_key, page_num, user_meh_genres_loop_copy[index], hated_list))
      this_one = ["PAGE", page_num, "INDEX", index, "A MEH'D"]      
      del user_meh_genres_loop_copy[index]
    else:
      index = random.randint(0, (len(user_loved_genres) - 1))
      this_one = ["PAGE", page_num, "INDEX", index, "A RANDO"]
      r = requests.get("https://api.themoviedb.org/3/discover/movie?api_key={}&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page={}&with_genres={}&with_runtime.gte=20&release_date.lte=2020-04-01".format(TMDB_key, page_num, user_loved_genres[index]))

    tmdb_result = json.loads(r.text)
    results = tmdb_result["results"]
    
    counter = 0

    while counter < len(results):
      if results[counter]['id'] in suggested_ids:
        print("I WAS IN HERE", results[counter]["title"])
        del results[counter]
      else:
        counter += 1
        
    all_results += results

  print("IT SUCCESSFULLY SEARCHED", this_one)
  selected_result = all_results[(random.randint(0, (len(all_results) - 1)))]

  details_r = requests.get("https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US".format(selected_result["id"], TMDB_key))
  detailed_result = json.loads(details_r.text)
  imdb_id = detailed_result["imdb_id"]
  runtime = detailed_result["runtime"]
  if selected_result["poster_path"]:
    poster = "https://image.tmdb.org/t/p/w500" + selected_result["poster_path"]
  else:
    poster = "images/noposter.png"

  ratingText = ''
  if imdb_id:
    imdb_link = "https://www.imdb.com/title/{}/".format(imdb_id)
    imdb_details = requests.get(imdb_link)
    tree = html.fromstring(imdb_details.content)

    try:
      rating = tree.xpath('//*[@id="title-overview-widget"]/div[1]/div[2]/div/div[1]/div[1]/div[1]/strong/span/text()')
    except:
      print("A scraping error occured")
      ratingText = "No IMDB rating available."

    if len(rating) > 0:
      ratingText = str(rating[0]) + '/10 on IMDB'
  else:
    imdb_link = "No IMDB link available."
    

  movie_info = {
    "title": selected_result["title"],
    "poster": poster,
    "description": selected_result["overview"],
    "release_date": selected_result["release_date"][:4],
    "tmdb_id": selected_result["id"],
    "imdb_link": imdb_link,
    "runtime" : runtime,
    "rating" : ratingText
  }

  movie_info_json = json.dumps(movie_info)
  return movie_info_json

@app.route("/api/users")
def users():
  users = User.query.all()
  user_list = []
  for user in users:
    user_list.append({"id":user.id, "name":user.name, "icon":user.icon})
  
  res = {
    "users": user_list
  }
  res_json = json.dumps(res)

  return res_json

@app.route("/api/genres")
def genres():
  genres = Genre.query.all()
  genre_arr = []
  for genre in genres:
    genre_arr.append({"id": genre.genre_api_id, "name": genre.genre_name})

  genres_json = json.dumps(genre_arr)
  return genres_json

@app.route("/api/friend<user>/genres")
def friendGenres(user):
  name = User.query.filter(User.name == user).one_or_none()
  genres = {"love":[], "hate":[]}

  for genre in name.user_genres:
    if genre.preference == True:
      genres["love"].append(genre.genre.genre_name)
    if genre.preference == False:
       genres["hate"].append(genre.genre.genre_name)
  res_json = json.dumps(genres)
  return res_json

@app.route("/api/<user>/genres", methods=['GET', 'POST'])
def userGenres(user):
  user = User.query.filter(User.name == user).one_or_none()

  if request.method == 'POST':
    req = json.loads(request.data)
    genre = Genre.query.filter(Genre.genre_api_id == req['id']).first()

    update_genre = User_genre.query.filter(User_genre.user_id == user.id, User_genre.genre_id == genre.id).first()

    if not update_genre:
      update_genre = User_genre(user_id = user.id, genre_id = genre.id)

    if req['preference'] == "":
      update_genre.preference = None
    else:
      update_genre.preference = req['preference']

    db.session.add(update_genre)
    db.session.commit()

  genres = []

  for genre in user.user_genres:
    genres.append(
      {
        "id": genre.genre.genre_api_id,
        "preference": genre.preference
      }
    )

  res = {
    "genres": genres
  }

  res_json = json.dumps(res)

  return res_json

@app.route("/api/<user>/genresreset", methods=['POST'])
def resetGenres(user):
  user = User.query.filter(User.name == user).one_or_none()
  
  genres = []

  for genre in user.user_genres:
    genre.preference = None
    db.session.add(genre)
    db.session.commit()
    
    genres.append(
      {
        "id": genre.genre.genre_api_id,
        "preference": genre.preference
      }
    )

  res = {
    "genres": genres
  }

  res_json = json.dumps(res)

  return res_json


@app.route("/api/<user>/favmovies", methods=['GET', 'POST', 'DELETE'])
def userFavmovies(user):
  dbUser = User.query.filter(User.name == user).one_or_none()
  userFavMovies = dbUser.favorited_movies

  if request.method == 'POST':
    req = json.loads(request.data)

    title = req['movie']['title']
    image = req['movie']['poster']
    description = req['movie']['description']
    movie_api_id = req['movie']['tmdbId']

    new_movie = Movie.query.filter(Movie.movie_api_id == str(movie_api_id)).first()

    if new_movie == None:
      new_movie = Movie(title = title, movie_api_id = movie_api_id, image = image, description = description)    
      db.session.add(new_movie)
      db.session.commit()

    previously_faved = Favorited_movie.query.filter(Favorited_movie.user_id == dbUser.id, Favorited_movie.movie_id == new_movie.id).one_or_none()
    if previously_faved == None:
      new_fave_movie = Favorited_movie(user_id = dbUser.id, movie_id = new_movie.id)
      db.session.add(new_fave_movie)
      db.session.commit()

  if request.method == 'DELETE':
    req = json.loads(request.data)

    remove_movie = Favorited_movie.query.filter(Favorited_movie.movie_id == req['id']).first()

    db.session.delete(remove_movie)
    db.session.commit()

  favorited_movies = []

  
  for fave_movie in dbUser.favorited_movies:
    favorited_movies.append(
      {
        "id": fave_movie.movie.id,
        "title": fave_movie.movie.title,
        "description": fave_movie.movie.description,
        "img": fave_movie.movie.image
      }
    )

  res = {
    "favorited_movies": favorited_movies
  }

  res_json = json.dumps(res)

  return res_json

@app.route("/api/<user>/latermovies", methods=['GET', 'POST', 'DELETE'])
def userLatemovies(user):

  dbUser = User.query.filter(User.name == user).one_or_none()
  userLaterMovies = dbUser.later_movies

  if request.method == 'POST':
    req = json.loads(request.data)
    title = req['suggestedMovie']['title']
    image = req['suggestedMovie']['poster']
    description = req['suggestedMovie']['description']
    movie_api_id = req['suggestedMovie']['tmdbId']

    new_movie = Movie.query.filter(Movie.movie_api_id == str(movie_api_id)).first()

    if new_movie == None:
      new_movie = Movie(title = title, movie_api_id = movie_api_id, image = image, description = description)    
      db.session.add(new_movie)
      db.session.commit()

    previously_latered = Later_movie.query.filter(Later_movie.user_id == dbUser.id, Later_movie.movie_id == new_movie.id).one_or_none()
    if previously_latered == None:
      new_later_movie = Later_movie(user_id = dbUser.id, movie_id = new_movie.id)
      db.session.add(new_later_movie)
      db.session.commit()

  if request.method == 'DELETE':
    req = json.loads(request.data)

    remove_movie = Later_movie.query.filter(Later_movie.movie_id == req['id']).first()

    db.session.delete(remove_movie)
    db.session.commit()

  later_movies = []
  for later_movie in dbUser.later_movies:
    later_movies.append(
      {
        "id": later_movie.movie.id,
        "title": later_movie.movie.title,
        "description": later_movie.movie.description,
        "img": later_movie.movie.image
      }
    )

  res = {
    "later_movies": later_movies
  }

  res_json = json.dumps(res)

  return res_json

@app.route("/movies/title/")
def title():
  movie_title = request.args['title']

  movies = requests.get("https://api.themoviedb.org/3/search/movie?api_key={}&language=en-US&query={}&page=1&include_adult=false".format(TMDB_key, movie_title))
  movies_dict = movies.json()
  
  if movies_dict['total_results'] == 0:
    no_movies = {
      'error': 'No movies were found for your search'
    }

    no_movies_json = json.dumps(no_movies)
    return no_movies_json
  
  results = movies_dict["results"]
  movies = []

  for result in results: 
    result_title = result["title"]
    if result["poster_path"]:
      result_poster = "https://image.tmdb.org/t/p/w500" + result["poster_path"]
    else:
      result_poster = "images/noposter.png"

    if 'release_date' not in result:
      result_release_date = ""
    else:
      result_release_date = result["release_date"][:4]
  
    result_description = result["overview"]
    result_tmdb_id = result["id"]

    movie_info = {
      "title": result_title,
      "poster": result_poster,
      "description": result_description,
      "release_date": result_release_date,
      "tmdbId": result_tmdb_id
    }

    movies.append(movie_info)

    res = {
      "movies": movies
    }

  movies_json = json.dumps(res)
  return movies_json

@app.route("/signup", methods=['POST'])
def signup():
  req = json.loads(request.data)

  user = User.query.filter(User.name == req['name']).one_or_none()
  if user != None:
    return make_response(jsonify({ "error": "Username already exists." })), 401

  num = random.randint(1, 4)
  user = User(name=req['name'], icon="images/user{}.png".format(num))
  user.set_password(req['password'])

  db.session.add(user)
  db.session.commit()

  for new_genre in req['genres']:
    genre = Genre.query.filter(Genre.genre_api_id == new_genre['id']).first()
    update_genre = User_genre(user_id = user.id, genre_id = genre.id)

    if new_genre['preference'] == "":
      update_genre.preference = None
    else:
      update_genre.preference = new_genre['preference']

    db.session.add(update_genre)

  db.session.commit()

  token = user.generate_token(user.id)

  user_info = {
    "id": user.id,
    "name": user.name,
    "avatar": user.icon,
    "token": token.decode()
  }

  res = {
    "user": user_info,
  }

  res_json = json.dumps(res)

  return res_json

@app.route("/login", methods=['GET', 'POST'])
def login():
  req = json.loads(request.data)

  user = User.query.filter(User.name == req['name']).one_or_none()
  if user == None or not user.check_password(req['password']):
    return make_response(jsonify({ "error": "Invalid password." })), 401

  genres = []

  for genre in user.user_genres:
    genres.append(
      {
        "id": genre.genre.genre_api_id,
        "preference": genre.preference
      }
    )

  token = user.generate_token(user.id)

  userInfo = {
    "id": user.id,
    "name": user.name,
    "avatar": user.icon,
    "token": token.decode()
  }

  later_movies = []

  for later_movie in user.later_movies:
    later_movies.append(
      {
        "id": later_movie.movie.id,
        "title": later_movie.movie.title,
        "description": later_movie.movie.description,
        "img": later_movie.movie.image
      }
    )

  favorited_movies = []

  for fave_movie in user.favorited_movies:
    favorited_movies.append(
      {
        "id": fave_movie.movie.id,
        "title": fave_movie.movie.title,
        "description": fave_movie.movie.description,
        "img": fave_movie.movie.image
      }
    )

  res = {
    "user": userInfo,
    "genres": genres,
    "later_movies": later_movies,
    "favorited_movies": favorited_movies
  }

  res_json = json.dumps(res)

  return res_json
