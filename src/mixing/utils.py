import eyed3

def get_metadata(metadata_df):
    show_data=metadata_df[['show_name','dj_name','show_nr','tags-0-tag']].dropna(axis=1, how='all').to_dict('records')
    show_data=show_data[0]
    show_name=show_data['show_name']
    dj_name=show_data['dj_name']
    ep_nr=show_data['show_nr']
    genre=show_data['tags-0-tag']
    return show_name, dj_name, ep_nr, genre

def get_filename(tag, show_name, dj_name, ep_nr, date):
    filename=f"{date}_{tag}_{show_name}_{ep_nr}_{dj_name}.mp3"
    return filename.replace(" ", "_").replace("/", "")

def add_metadata_to_mp3(file_path, show_name, dj_name, ep_nr, genre, year):
    # Load the MP3 file
    audiofile = eyed3.load(file_path)
    
    # Set metadata
    audiofile.tag.artist = dj_name
    audiofile.tag.title = show_name
    audiofile.tag.album = show_name
    audiofile.tag.release_date = year
    audiofile.tag.track_num = (ep_nr, None)  # (track_number, total_tracks)
    audiofile.tag.genre = genre
    
    # Save changes
    audiofile.tag.save()

