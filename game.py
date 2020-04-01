from configparser import ConfigParser
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from pygame.math import Vector2
import os
import json
import pygame

# Константы
config_file = 'settings.ini'
grid_size = 1
color_text = ( 255, 255, 255 )
color_background = ( 40, 40, 40 )
color_grid = ( 80, 80, 80 )
color_selected_ceil = ( 180, 180, 180 )
color_alive_ceil = ( 255, 255, 255 )

def load_config():
	global width
	global height
	global field_size
	
	# Проверка на существование конфига
	if os.path.exists(config_file):
		config = ConfigParser()
		config.read(config_file)
		
		# Загружаем переменные из конфига
		width = int(config['Settings']['width'])
		height = int(config['Settings']['height'])
		field_size = [
			int(config['Settings']['field_width']),
			int(config['Settings']['field_height'])
		]
	else:
		# Задаем стандартные значения
		width = 640
		height = 480
		field_size = [ 100, 100 ]
		
		config = ConfigParser()
		config['Settings'] = {
			'width': width,
			'height': height,
			'field_width': field_size[0],
			'field_height': field_size[1]
		}

		# Сохраняем
		with open(config_file, 'w') as file:
			config.write(file)
		

def init():
	global display
	global font

	load_config()
	
	Tk().withdraw()
	pygame.init()
	pygame.font.init()
	display = pygame.display.set_mode((width, height))	# Создаем окно
	font = pygame.font.Font('font.ttf', 13)				# Загружаем шрифт
	

def start():
	global is_game_started
	global game_speed
	global counter
	global selected_tile
	global ceil_size
	global camera
	global is_camera_moving
	global field_editing_state
	
	generate_level(field_size[0], field_size[1])
	
	ceil_size = 50					# Размер одной клетки в пикселях
	camera = Vector2(0.0, 0.0)		# Позиция камеры единицей считается размер одной клетки
	game_speed = 1.0				# Скорость игры
	counter = 0						# Счетчик ходов
	selected_tile = None			# Текущая выделенная клетка

	is_quit = False					# Состояние окна
	is_game_started = False			# Запущена ли игра
	update_time = 0
	is_camera_moving = False		# Двигается ли камера
	field_editing_state = 0			# Изменяется ли поле
	
	# Главный цикл
	while not is_quit:
		display.fill(color_background)
		draw_field()
		draw_info()
		pygame.display.update()
		
		ticks = pygame.time.get_ticks()
		
		# Если игра запущена и прошло время для начала следующего шага
		if is_game_started and ticks - update_time > 100.0 * game_speed:
			make_step()
			update_time = ticks
	
		# Обработка событий
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				is_quit = True
			else:
				handle_event(event)
	pygame.quit()
	
	
# Загрузить уровень из файла
def load_level(path):
	global field_size
	global field

	with open(path, 'r') as file:
		data = json.load(file)
		field_size = [
			data['width'],
			data['height']
		]
		field = data['ceils']
		
		
# Сохранить уровень в указанную директорию
def save_level(path):
	global field_size
	global field
	with open(path, 'w') as file:
		json.dump({
			'width': field_size[0],
			'height': field_size[1],
			'ceils': field
		}, file)
	

# Сгенерировать уровень
def generate_level(size_x, size_y):
	global field
	field = [[ 0 for i in range(size_y) ] for i in range(size_x)]
	
	
# Функция обработки событий
def handle_event(event):
	global game_speed
	global is_game_started
	global camera
	global ceil_size
	global selected_tile
	global is_camera_moving
	global field_editing_state

	if event.type == pygame.KEYDOWN:
		if event.key == pygame.K_EQUALS:	# Нажата кнопка '+'
			game_speed -= 0.5
			if game_speed < 0.0:
				game_speed = 0.0
		elif event.key == pygame.K_MINUS:	# Нажата кнопка '-'
			game_speed += 0.5
		elif event.key == pygame.K_SPACE:	# Нажат пробел
			is_game_started = not is_game_started
		elif event.key == pygame.K_RIGHT:	# Нажата стрелка влево
			if not is_game_started:
				make_step()
		elif event.key == pygame.K_c:		# Нажата буква 'C'
			if not is_game_started:
				generate_level(field_size[0], field_size[1])
		elif event.key == pygame.K_l:		# Нажата буква 'L'
			if not is_game_started:
				path = askopenfilename(initialdir=os.getcwd(), 
					filetypes=[
						('JSON file', '*.json')
					],
					defaultextension='.json')
				if os.path.exists(path):
					load_level(path)
		elif event.key == pygame.K_s:		# Нажата буква 'S'
			if not is_game_started:
				path = asksaveasfilename(initialdir=os.getcwd(), 
					filetypes=[
						('JSON file', '*.json')
					],
					defaultextension='.json')
				if path != '':
					save_level(path)
	elif event.type == pygame.MOUSEBUTTONDOWN:
		if event.button == 1:	# Нажата левая кнопка мыши
			field_editing_state = 1
			if selected_tile != None and not is_game_started:
				field[selected_tile[0]][selected_tile[1]] = 1
				counter = 0
		elif event.button == 2:	# Нажата средняя кнопка мыши
			is_camera_moving = True
		elif event.button == 3:	# Нажата правая кнопка мыши
			field_editing_state = 2
			if selected_tile != None and not is_game_started:
				field[selected_tile[0]][selected_tile[1]] = 0
				counter = 0
		elif event.button == 4:	# Прокручено колёсеко вперед
			ceil_size += 1
		elif event.button == 5:	# Прокручено колёсеко назад
			ceil_size -= 1
			if ceil_size <= 10:
				ceil_size = 10
	elif event.type == pygame.MOUSEBUTTONUP:
		if event.button == 1:	# Отпущена левая кнопка мыши
			field_editing_state = 0
		elif event.button == 2:	# Отпущена средняя кнопка мыши
			is_camera_moving = False
		elif event.button == 3:	# Отпущена правая кнопка мыши
			field_editing_state = 0
	elif event.type == pygame.MOUSEMOTION:
		if is_camera_moving:
			camera -= Vector2(event.rel[0] / ceil_size, event.rel[1] / ceil_size)
			if camera.x < -field_size[0]:
				camera.x = -field_size[0]
			elif camera.x > field_size[0] * 2:
				camera.x = field_size[0] * 2
			if camera.y < -field_size[1]:
				camera.y = -field_size[1]
			elif camera.y > field_size[1] * 2:
				camera.y = field_size[1] * 2
		mouse_pos = convert_screen_to_world(Vector2(event.pos[0], event.pos[1]))
		if mouse_pos.x > 0.0 and mouse_pos.x < field_size[0] and mouse_pos.y > 0.0 and mouse_pos.y < field_size[1]:
			selected_tile = [ int(mouse_pos.x), int(mouse_pos.y) ]
			if not is_game_started:
				if field_editing_state == 1:
					field[selected_tile[0]][selected_tile[1]] = 1
					counter = 0
				elif field_editing_state == 2:
					field[selected_tile[0]][selected_tile[1]] = 0
					counter = 0
		else:
			selected_tile = None


# Нарисовать поле
def draw_field():
	# Рисуем вертикальную сетку
	for x in range(field_size[0] + 1):
		position = convert_world_to_screen(Vector2(x, 0))
		pygame.draw.rect(display, color_grid, (position.x - grid_size * 0.5, position.y, grid_size, field_size[1] * ceil_size))
		
	# Рисуем горизонтальную сетку
	for y in range(field_size[1] + 1):
		position = convert_world_to_screen(Vector2(0, y))
		pygame.draw.rect(display, color_grid, (position.x, position.y - grid_size * 0.5, field_size[0] * ceil_size, grid_size))
		
	# Рисуем живие клетки
	for x in range(field_size[0]):
		for y in range(field_size[1]):
			if field[x][y] == 1:
				position = convert_world_to_screen(Vector2(x, y))
				pygame.draw.rect(display, color_alive_ceil, (
					position.x + ceil_size * 0.1,
					position.y + ceil_size * 0.1,
					ceil_size * 0.8, ceil_size * 0.8))
		
	# Рисуем выделенную клетку
	if selected_tile != None and not is_game_started:
		position = convert_world_to_screen(Vector2(selected_tile[0], selected_tile[1]))
		pygame.draw.rect(display, color_selected_ceil, (
			position.x + ceil_size * 0.1,
			position.y + ceil_size * 0.1,
			ceil_size * 0.8, ceil_size * 0.8))
		
		
# Написать текст
def draw_info():
	if is_game_started:
		draw_text('SPACE - to pause', 5, height - 60)
		draw_text('\'+\' - to speed up', 5, height - 40)
		draw_text('\'-\' - to slow down', 5, height - 20)
	else:
		draw_text('SPACE - to start', 5, height - 140)
		draw_text('C - to clear field', 5, height - 120)
		draw_text('S - to save', 5, height - 100)
		draw_text('L - to load', 5, height - 80)
		draw_text('\'->\' - to make one step', 5, height - 60)
		draw_text('\'+\' - to speed up', 5, height - 40)
		draw_text('\'-\' - to slow down', 5, height - 20)
	draw_text('Game speed: {0:0.1f}'.format(game_speed), 200, height - 20)
	draw_text('Counter: {0}'.format(counter), 400, height - 20)
		
		
# Написать текст на экране
def draw_text(text, x, y):
	surface = font.render(text, True, color_text)
	display.blit(surface, (x, y))
	
	
# Сделать один ход
def make_step():
	global counter
	global field
	
	new_field = []
	for x in range(field_size[0]):
		new_field.append(field[x].copy())
		
	for x in range(field_size[0]):
		for y in range(field_size[1]):
			ceil = field[x][y]
			neighbors = get_neightbors(x, y)
			if ceil == 0:
				if neighbors == 3:
					new_field[x][y] = 1
			elif ceil == 1:
				if neighbors < 2 or neighbors > 3:
					new_field[x][y] = 0
	field = new_field
	counter += 1
	
	
# Получить кол-во соседей у клетки
def get_neightbors(x, y):
	count = 0
	if get_ceil(x + 1, y):
		count += 1
	if get_ceil(x + 1, y + 1):
		count += 1
	if get_ceil(x, y + 1):
		count += 1
	if get_ceil(x - 1, y + 1):
		count += 1
	if get_ceil(x - 1, y):
		count += 1
	if get_ceil(x - 1, y - 1):
		count += 1
	if get_ceil(x, y - 1):
		count += 1
	if get_ceil(x + 1, y - 1):
		count += 1
	return count
	
	
# Получить тип клетки по её координате
def get_ceil(x, y):
	if x < 0 or x >= field_size[0]:
		x %= field_size[0]
	if y < 0 or y >= field_size[1]:
		y %= field_size[1]
	return field[x][y]
		

# Конвертировать мировые координаты в экранные
def convert_world_to_screen(vector):
	return vector * ceil_size - camera * ceil_size + Vector2(width * 0.5, height * 0.5)
	

# Конвертировать экранные координаты в мированые
def convert_screen_to_world(vector):
	return vector / ceil_size - Vector2(width * 0.5, height * 0.5) / ceil_size + camera
	