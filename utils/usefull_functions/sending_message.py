from aiogram import Bot
import os


async def sending_function(
        bot: Bot, chat_id, text, audio, photo, video, video_note, document, markup=None
):
    print("Здесь бот")
    funnel_message = 0
    if photo is not None:
        try:
            funnel_message = await bot.send_photo(
                chat_id=chat_id,
                caption=text,
                photo=photo,
                parse_mode="html",
                reply_markup=markup,

            )
            
        except Exception as e:
            print(e)

    elif video_note is not None:
        try:
            funnel_message = await bot.send_video_note(
                chat_id=chat_id,
                video_note=video_note,
                reply_markup=markup
            )
        except Exception as e:
            print(e)

    elif video is not None:
        try:
            funnel_message = await bot.send_video(
                chat_id=chat_id,
                video=video,
                reply_markup=markup,
                caption=text,
                parse_mode="html"
            )
        except Exception as e:
            print(e)

    elif audio is not None:
        try:
            funnel_message = await bot.send_voice(
                chat_id=chat_id,
                voice=audio,
                reply_markup=markup
            )
        except Exception as e:
            print(e)

    elif document:
        try:
            filename = f"files/document/document.pdf"
            with open(filename, "wb") as pdf_file:
                pdf_file.write(document)

            with open(filename, "rb") as file:
                funnel_message = await bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    caption=text,
                    parse_mode="html",
                    reply_markup=markup,
                )

            os.remove(filename)
        except Exception as e:
            print(e)



    elif text is not None:
        try:
            funnel_message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="html",
                reply_markup=markup,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(e)

    return funnel_message