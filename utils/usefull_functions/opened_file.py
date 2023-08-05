import os

def open_files(audio_name=None, photo_name=None, video_name=None, video_note_name=None, document_name=None):
    audio_reader = None
    photo_reader = None
    video_reader = None
    video_note_reader = None
    document_reader = None

    audio = None
    photo = None
    video = None
    video_note = None
    document = None

    try:
        if audio_name is not None:
            audio = open(audio_name, "rb")
            audio_reader = audio.read()
    except Exception as e:
        print(e)

    try:
        if photo_name is not None:
            photo = open(photo_name, "rb")
            photo_reader = photo.read()
    except Exception as e:
        print(e)

    try:
        if video_name is not None:
            video = open(video_name, "rb")
            video_reader = video.read()
    except Exception as e:
        print(e)

    try:
        if video_note_name is not None:
            video_note = open(video_note_name, "rb")
            video_note_reader = video_note.read()
    except Exception as e:
        print(e)

    try:
        if document_name is not None:
            document = open(document_name, "rb")
            document_reader = document.read()
    except Exception as e:
        print(e)

    if audio:
        audio.close()
        os.remove(audio_name)

    if photo:
        photo.close()
        os.remove(photo_name)

    if video:
        video.close()
        os.remove(video_name)

    if video_note:
        video_note.close()
        os.remove(video_note_name)

    if document:
        document.close()
        os.remove(document_name)

    return audio_reader, photo_reader, video_reader, video_note_reader, document_reader