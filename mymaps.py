import os
from win32api import GetSystemMetrics
import math
import pygame
import pygame_gui
import requests
import pprint
from dotenv import load_dotenv
import convert

path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(path):
    load_dotenv(path)

    APP_ID = os.environ.get('APP_ID')
    APP_ID2 = os.environ.get('APP_ID2')
WIDTH, HEIGHT = 600, 450
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
h, w = GetSystemMetrics(1), GetSystemMetrics(0)
manager = pygame_gui.UIManager((WIDTH, HEIGHT))


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


def lonlat_distance(a, b):

    degree_to_meters_factor = 111 * 1000  # 111 километров в метрах
    a_lon, a_lat = a
    b_lon, b_lat = b

    # Берем среднюю по широте точку и считаем коэффициент для нее.
    radians_lattitude = math.radians((a_lat + b_lat) / 2.)
    lat_lon_factor = math.cos(radians_lattitude)

    # Вычисляем смещения в метрах по вертикали и горизонтали.
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor

    # Вычисляем расстояние между точками.
    distance = math.sqrt(dx * dx + dy * dy)

    return distance


def address_by_coord(coord):
    geocoder_request = f"https://geocode-maps.yandex.ru/1." \
        f"x/?apikey=40d1649f-0493-4b70-98ba-98533de7" \
        f"710b&geocode={coord}&format=json"
    # Выполняем запрос.
    r = requests.get(geocoder_request)
    if r:
        json = r.json()
        addres = json['response'][
            'GeoObjectCollection']['featureMember'][0][
            'GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']
        address_text = addres['formatted']
        return address_text
    else:
        print("Ошибка выполнения запроса:")
        print(geocoder_request)
        print("Http статус:", r.status_code, "(", r.reason, ")")


def get_type_map():
    global type_m
    index = available_type.index(type_m)
    index += 1
    if index >= len(available_type):
        index = 0
    type_m = available_type[index]
    return type_m


def get_nearst_biz_by_metka():
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = APP_ID
    # print(list(reversed(list(metka.split(',')))))
    search_params = {
        "apikey": api_key,
        "text": address_by_coord(metka),
        "lang": "ru_RU",
        "ll": metka,
        'spn': '0.0005,0.0005',
        "type": "biz"
    }
    response = requests.get(search_api_server, params=search_params)
    if not response:
        print("Ошибка выполнения запроса:")
        print(response)
        print("Http статус:", response.status_code, "(", response.reason, ")")
    else:
        json_response = response.json()
        for biz in json_response['features']:
            if lonlat_distance(biz['geometry']['coordinates'],
                               list(map(float, metka.split(',')))) <= 50:
                address_label.set_text(biz['properties']['name'])
                show_picture(biz=','.join(list(map(str, biz['geometry'][
                                                           'coordinates']))))
                return


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
        metka = ','.join(list(map(str, coordinates)))

        is_metka_hidden = False
        address_label.visible = True
        coords = metka
        get_addres_and_postal_number(metka)
        return metka
    return coords


def get_addres_and_postal_number(pos):
    global is_hidden_postal_number
    if not is_metka_hidden:
        is_hidden_postal_number = not is_hidden_postal_number
        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "apikey": APP_ID2,
            "geocode": pos,
            "format": "json"}

        response = requests.get(geocoder_api_server, params=geocoder_params)
        if not response:
            print("Ошибка выполнения запроса:")
            print(response)
            print("Http статус:", response.status_code, "(", response.reason,
                  ")")
        else:
            json_response = response.json()
            # pprint.pprint(json_response)
            addres = json_response['response'][
                'GeoObjectCollection']['featureMember'][0][
                'GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']
            address_text = addres['formatted']
            address_label.set_text(address_text)
            if 'postal_code' in addres and not is_hidden_postal_number:
                postal_code = addres['postal_code']
                text = address_label.text
                address_label.set_text(f'{text} - {postal_code}')


def get_metka_pos(pos):
    if pos is None:
        return ''
    global is_metka_hidden, metka
    is_metka_hidden = False
    x, y = pos
    centerx, centery = WIDTH // 2, HEIGHT // 2
    long, latt = list(map(float, coords.split(',')))
    deltax = centerx - x
    deltay = centery - y
    x2, y2 = convert.ll2px(latt, long, zoom_map)
    x2 += -deltax
    y2 += -deltay
    latt2, long2 = convert.px2ll(x2, y2, zoom_map)
    metka = ','.join([str(long2), str(latt2)])
    return f"{metka},vkbkm"


def show_picture(search_text=None, scale=None,
                 move=None, type_map=None, mouse=None, biz=None):
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
    if search_text is not None and mouse is None:
        coords = search_obj(search_text)
    if mouse is not None:
        get_metka_pos(mouse)
        get_addres_and_postal_number(metka)
        address_label.visible = True
    st = '' if biz is None else f"~{biz},pm2blywl"
    map_params = {
        'l': type_m if type_map is None else get_type_map(),
        'll': coords,
        'z': zoom_map,
        "pt": f"{metka},vkbkm{st}" if not is_metka_hidden else ''
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
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                get_nearst_biz_by_metka()
            if event.button == 1:
                show_picture(mouse=(pygame.mouse.get_pos()))
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
            elif event.key == pygame.K_p:
                get_addres_and_postal_number(metka)
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
                    get_addres_and_postal_number(metka)
        manager.process_events(event)
    screen.fill((0, 0, 0))
    screen.blit(pygame.image.load(map_file), (0, 0))

    manager.update(time_delta)
    manager.draw_ui(screen)

    pygame.display.flip()
    clock.tick(FPS)
pygame.quit()

os.remove(map_file)
