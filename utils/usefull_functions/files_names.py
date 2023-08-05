
async def files_names(message, token, bot):
    photo_name = None
    text = None
    audio_name = None
    video_name = None
    video_note_name = None
    document_name = None

    if message.photo:
        await message.photo[-1].download(f"files/photo/{token}start_photo.jpg")
        photo_name = f"files/photo/{token}start_photo.jpg"
        if message.caption:
            text = message.html_text

    elif message.voice:
        await message.voice.download(f"files/audio/{token}start_voice.ogg")
        audio_name = f"files/audio/{token}start_voice.ogg"

    elif message.video:
        await message.video.download(f"files/video/{token}start_video.mp4")
        video_name = f"files/video/{token}start_video.mp4"

        if message.caption:
            text = message.html_text

    elif message.video_note:
        await message.video_note.download(f"files/video_note/{token}start_video_note.mp4")
        video_note_name = f"files/video_note/{token}start_video_note.mp4"

    elif message.document:
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path

        if file_path.endswith(".pdf"):
            await message.document.download(f"files/document/{token}document.pdf")
            document_name = f"files/document/{token}document.pdf"

            if message.caption:
                text = message.html_text

    elif message.text:
        text = message.html_text


    return text, audio_name, photo_name, video_name, video_note_name, document_name