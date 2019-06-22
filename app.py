import time
from random import normalvariate

from flask import Flask
from flask import redirect, render_template, request
from flask import send_from_directory, session, stream_with_context, url_for

from blockoff import * 

TOKEN = load_token()

app = Flask(__name__)

def stdev(A, mean):
    '''
    Returns standard deviation of values in A.
    Treats values in A as samples from a population.
    '''
    residuals = [(mean - x)**2 for x in A]
    var = sum(residuals) / (len(A) - 1)
    stdev = math.sqrt(var)
    return stdev

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/find')
def find():
    if 'artist' not in request.args.keys():
        return redirect(url_for('index'))

    artist = request.args.get('artist').strip().lower().replace(' ', '-')
    if artist == '':
        return redirect(url_for('index'))

    try:
        artist_id = load_artist_id(artist)
        add_to_manifest(artist, artist_id)
        return render_template('index.html', found=True, artist_data=(artist, artist_id))
    except:
        return render_template('index.html', found=False, artist_data=(artist, None))

@app.route('/generate')
def generate():
    if 'artist' not in request.args.keys():
        return redirect(url_for('index'))
    artist = request.args.get('artist')

    if 'artist_id' not in request.args.keys():
        return redirect(url_for('find', artist=request.args.get('artist')))
    artist_id = request.args.get('artist_id')

    if 'ngrams' not in request.args.keys():
        return render_template('index', found=True, artist_data=(artist, artist_id))

    i = 0
    count = song_count(artist_id, TOKEN)
    songs = []
    for song in load_songs(artist_id, TOKEN):
        songs.append(song)
        i += 1

    # new song length sampled from normal distribution based on other songs
    song_lengths = [len(s) for s in songs]
    mean_line_count = sum(song_lengths) / len(songs)
    sd = stdev(song_lengths, mean_line_count)
    sample_length = normalvariate(mean_line_count, sd)

    chain = build_chain(songs)
    lines = generate_song(chain, sample_length).split('\n')
    return render_template('song.html', 
                           found=True, 
                           artist_data=(artist, artist_id), 
                           lines=lines)

if __name__ == "__main__":
    app.secret_key = '123'
    app.run(debug=True)
