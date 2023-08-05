from requests import request
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_markup(markup_text, markup: InlineKeyboardMarkup, commands_list):
    if markup_text == "0" or markup_text is None:
        return None

    if commands_list is None:
        commands_list = []

    row_list = markup_text.split("\n")

    for row in row_list:
        if "&&" in row:
            LWS = row.split("&&")

            magic_dict = {}
            status = "0"
            for elem in LWS:
                try:
                    text, url = elem.split("-")
                except ValueError:
                    text, url = elem.split("–")

                text = text.strip()
                url = url.strip()

                try:
                    http_url = "https://" + url if "https://" not in url else url
                    status = request("GET", http_url).status_code

                except Exception as e:
                    print(e)

                if status == 200:
                    magic_dict[url] = "url"

                elif url in commands_list:
                    magic_dict[url] = "command"

                elif url not in commands_list:
                    magic_dict[url] = "/start"

            try:
                text1, url1 = list(map(lambda x: x.strip(), LWS[0].split('-')))
            except ValueError:
                text1, url1 = list(map(lambda x: x.strip(), LWS[0].split('–')))

            try:
                text2, url2 = list(map(lambda x: x.strip(), LWS[1].split('-')))
            except ValueError:
                text2, url2 = list(map(lambda x: x.strip(), LWS[1].split('–')))

            if magic_dict[url1] == "url" and magic_dict[url2] == "url":
                    markup.add(
                        InlineKeyboardButton(
                            text=text1,
                            url=url1
                        ),
                        InlineKeyboardButton(
                            text=text2,
                            url=url2
                        )
                    )

            elif magic_dict[url1] == "url" and magic_dict[url2] != "url":
                if magic_dict[url2] == "/start":
                    url2 = "/start"

                markup.add(
                    InlineKeyboardButton(
                        text=text1,
                        url=url1
                    ),
                    InlineKeyboardButton(
                        text=text2,
                        callback_data=url2
                    )
                )

            elif magic_dict[url2] == "url" and magic_dict[url1] != "url":
                if magic_dict[url1] == "/start":
                    url1 = "/start"

                markup.add(
                    InlineKeyboardButton(
                        text=text1,
                        callback_data=url1
                    ),
                    InlineKeyboardButton(
                        text=text2,
                        url=url2
                    )
                )

            elif magic_dict[url1] != "url" and magic_dict[url2] != "url":
                if magic_dict[url1] == "/start":
                    url1 = "/start"

                if magic_dict[url2] == "/start":
                    url2 = "/start"

                markup.add(
                    InlineKeyboardButton(
                        text=text1,
                        callback_data=url1
                    ),
                    InlineKeyboardButton(
                        text=text2,
                        callback_data=url2
                    )
                )
        else:
            LWS = row

            try:
                text, url = LWS.split("-")
            except ValueError:
                text, url = LWS.split("–")
                
            text = text.strip()
            url = url.strip()

            status = "0"
            try:
                http_url = "https://" + url if "https://" not in url else url
                status = request("GET", http_url).status_code
            except Exception as e:
                print(e)

            if status == 200:
                markup.add(
                    InlineKeyboardButton(
                        text=text,
                        url=url
                    )
                )

            elif url in commands_list:
                markup.add(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=url
                    )
                )

            elif url not in commands_list:
                markup.add(
                    InlineKeyboardButton(
                        text=text,
                        callback_data="/start"
                    )
                )

    return markup

