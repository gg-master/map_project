import os
from win32api import GetSystemMetrics
import math
import pygame
import pygame_gui
import requests
import pprint
from dotenv import load_dotenv

path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(path):
    load_dotenv(path)

    APP_ID = os.environ.get('APP_ID')
    APP_ID2 = os.environ.get('APP_ID2')

pygame.init()
screen = pygame.display.set_mode((600, 450))
h, w = GetSystemMetrics(1), GetSystemMetrics(0)
manager = pygame_gui.UIManager((600, 450))


user_input = input('Введите долготу и широту '
                   '(по умолчанию 44.559173,48.527201): ')
coords = '44.559173,48.527201' \
    if not user_input else user_input
zoom_map = 18
type_m = 'map'
available_type = ['map', 'sat', 'skl', 'trf']

entry = pygame_gui.elements.UITextEntryLine(
    relative_rect=pygame.Rect((0, 0), (100, 30)), manager=manager
)
clear_metka = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((100, 0), (50, 30)),
    manager=manager,
    text='Clear'
)
address_label = pygame_gui.elements.ui_label.UILabel(
    relative_rect=pygame.Rect((0, 450 - 60), (600, 30)),
    text='Address',
    manager=manager,
    visible=False
)
postal_trigger = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((600 - 100, 450 - 90), (100, 30)),
    manager=manager,
    text='Postal numb'
)
is_metka_hidden = True
is_hidden_postal_number = True
metka = coords


def get_type_map():
    global type_m
    index = available_type.index(type_m)
    index += 1
    if index >= len(available_type):
        index = 0
    type_m = available_type[index]
    return type_m


def search_obj(search_text):
    global metka, is_metka_hidden, coords
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = APP_ID
    search_params = {
        "apikey": api_key,
        "text": search_text,
        "lang": "ru_RU",
    }
    response = requests.get(search_api_server, params=search_params)
    if not response:
        print("Ошибка выполнения запроса:")
        print(response)
        print("Http статус:", response.status_code, "(", response.reason, ")")
    else:
        json_response = response.json()
        # pprint.pprint(json_response)
        element = json_response['features'][0]
        coordinates = element['geometry']['coordinates']
        address = element['properties'][
            'GeocoderMetaData']['text']
        address_label.set_text(address)
        metka = ','.join(list(map(str, coordinates)))
        is_metka_hidden = False
        address_label.visible = True
        coords = metka
        get_postal_number()
        return metka
    return coords


def get_postal_number():
    global is_hidden_postal_number
    if not is_metka_hidden:
        is_hidden_postal_number = not is_hidden_postal_number
        if is_hidden_postal_number:
            text = address_label.text
            address_label.set_text(''.join(text.split(' - ')[0]))
            return
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "apikey": APP_ID2,
            "geocode": coords,
            "format": "json"}

        response = requests.get(geocoder_api_server, params=geocoder_params)
        if not response:
            print("Ошибка выполнения запроса:")
            print(response)
            print("Http статус:", response.status_code, "(", response.reason,
                  ")")
        else:
            json_response = response.json()
            addres = json_response['response'][
                'GeoObjectCollection']['featureMember'][0][
                'GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']
            if 'postal_code' in addres:
                postal_code = addres['postal_code']
                text = address_label.text
                address_label.set_text(f'{text} - {postal_code}')


def show_picture(search_text=None, scale=None, move=None, type_map=None):
    global zoom_map, coords, is_metka_hidden
    if scale is not None:
        zoom_map = min(19, max(zoom_map + scale, 5))
    if move is not None:
        long, latt = map(float, coords.split(','))
        if move == 'up':
            latt = max(-90, min(90, latt + math.radians(h) / 180))
        if move == 'down':
            latt = max(-90, min(90, latt - math.radians(h) / 180))
        if move == 'left':
            long = max(-180, min(180, long - math.radians(w) / 180))
        if move == 'right':
            long = max(-180, min(180, long + math.radians(w) / 180))
        coords = ','.join([str(long), str(latt)])
    if search_text is not None:
        coords = search_obj(search_text)
    map_params = {
        'l': type_m if type_map is None else get_type_map(),
        'll': coords,
        'z': zoom_map,
        "pt": "{0},vkbkm".format(metka) if not is_metka_hidden else ''
    }
    map_api_server = "http://static-maps.yandex.ru/1.x/"
    response = requests.get(map_api_server, params=map_params)
    if not response:
        print("Ошибка выполнения запроса:")
        print(response)
        print("Http статус:", response.status_code, "(", response.reason, ")")
    with open(map_file, "wb") as file:
        file.write(response.content)


map_file = 'map.png'
show_picture()
FPS = 60
clock = pygame.time.Clock()
running = True

response_timer = pygame.time.get_ticks()
while running:
    time_delta = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PAGEUP:
                show_picture(scale=1)
            elif event.key == pygame.K_PAGEDOWN:
                show_picture(scale=-1)
            elif event.key == pygame.K_UP:
                show_picture(move='up')
            elif event.key == pygame.K_DOWN:
                show_picture(move='down')
            elif event.key == pygame.K_LEFT:
                show_picture(move='left')
            elif event.key == pygame.K_RIGHT:
                show_picture(move='right')
            elif event.key == pygame.K_TAB:
                show_picture(type_map='next')
        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                if pygame.time.get_ticks() - response_timer > 3000:
                    show_picture(search_text=event.text)
                    response_timer = pygame.time.get_ticks()
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == clear_metka:
                    is_metka_hidden = True
                    address_label.visible = False
                    show_picture()
                if event.ui_element == postal_trigger:
                    get_postal_number()
        manager.process_events(event)
    screen.fill((0, 0, 0))
    screen.blit(pygame.image.load(map_file), (0, 0))

    manager.update(time_delta)
    manager.draw_ui(screen)

    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()

os.remove(map_file)
