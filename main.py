from kivy.app import App
from kivy.uix.widget import Widget
from kivy.config import Config
from kivy.uix.image import Image

from kivy.graphics import Bezier
from kivy.clock import Clock
Config.set('graphics', 'resizable', '0')
Config.set('input', 'mouse', 'mouse,disable_multitouch')
from kivy.core.window import Window

from settings import Settings
from ball import Ball
from player import Player
from block import Block
from functools import partial
from random import choice

settings = Settings()
Window.size = settings.window_size

class Game(Widget):
	player = Player()
	blocks = []
	angle_line_showing = True #Показывается ли сейчас линия угла (запуска)
	lightning_offset = 0 #Время, в течение которого бьёт молния!
	radiation_offset = 0
	bg_start = 0
	bg_end = 0
	bonuses = ['lightning', 'double', 'ignore', 'offset', 'speed', 'allballs',
		'random', 'damager', 'bifurcation', 'radiation'
			]

	def init_graphics(self):
		self.bg = Image(source='Data/bg.gif', pos=(0,0), size=Window.size, anim_loop=0, anim_delay = 0.05)
		self.add_widget(self.bg) #Добавление фона
		self.add_balls()
		self.draw_line()
		self.create_blocks_line()

	def add_balls(self):
		'''Добавляет мячи в список для мячей, а также выводит их на экран'''
		for i in range(self.player.balls_quantity):
			self.player.balls.append(Ball(settings, self))
			self.add_widget(self.player.balls[-1])
			self.player.balls[-1].draw_rect()

	def draw_line(self):
		self.angle_line = Bezier(points = (self.player.balls[-1].center_x, self.player.balls[-1].center_y,
		 self.player.balls[-1].center_x, self.player.balls[-1].center_y ), dash_length = 5, dash_offset = 5)
		self.canvas.add(self.angle_line)

	def create_blocks_line(self):
		for i in range(settings.blocks_quantity): 
			self.blocks.append(Block(settings, 'Block', self))
			self.add_widget(self.blocks[-1])
			self.add_widget(self.blocks[-1].label)
		self.blocks.append(Block(settings, 'ball', self))
		self.add_widget(self.blocks[-1])
		bonus = choice(self.bonuses)
		if bonus != 1:
			self.blocks.append(Block(settings, bonus, self))
			self.add_widget(self.blocks[-1])




	def update(self, dt):
		if self.bg_start > 0:
			self.bg_start -= 1
			if self.bg_start == 0:
				if self.lightning_offset > 0: self.bg.source = 'Data/lightning_bg.gif'
				elif self.radiation_offset > 0: self.bg.source = 'Data/radiation_bg.gif'
		if self.bg_end > 0:
			self.bg_end -= 1
		self.update_balls()
		self.check_new_step()
		self.update_blocks()
		self.big_bonus(self.lightning_offset, 'lightning', self.check_lightning)
		self.big_bonus(self.radiation_offset, 'radiation', self.check_radiation)

	def check_lightning(self):
		'''Действия молнии'''
		if self.lightning_offset % 20 == 0:
			rand_block = choice([i for i in range(len(self.blocks)) if self.blocks[i]._type == 'Block'])
			self.blocks[rand_block].get_damage(int(self.blocks[rand_block].health/5))

	def check_radiation(self):
		'''Действия радиации'''
		if self.radiation_offset % 60 == 0:
			for block in self.blocks:
				if block._type == 'Block': block.get_damage(1)

	def big_bonus(self, bonus_offset, bonus_name, handler):
		end = False
		if bonus_offset > 0 and self.bg_start == 0:
			handler()
			if bonus_name == 'radiation':
				self.radiation_offset -= 1
				if self.radiation_offset == 0: end = True
			else:
				self.lightning_offset -= 1
				if self.lightning_offset == 0: end = True
			if end:
				self.bg.source = 'Data/end_'+bonus_name+'_bg.gif'
				self.bg_end = 60
		elif self.lightning_offset == 0 and self.radiation_offset == 0 and self.bg_start == 0 and self.bg_end == 0:
			self.bg.source = 'Data/bg.gif'
			for ball in self.player.balls:
				ball.big_bonus = False	

	def update_balls(self):
		'''Обновляет мячи, проверяет коллизии'''
		for ball in self.player.balls:
			if ball.motion:
				ball.move()
				ball.check_collisions()
				if ball.ignore > 0: ball.ignore -= 1
				if ball.damager > 0: ball.damager -= 1
		if len(self.player.fake_balls) > 0:
			for ball in self.player.fake_balls:
				if ball.motion:
					ball.move()
					ball.check_collisions()
					if ball.y <= 0:
						self.player.fake_balls.remove(ball)
						self.remove_widget(ball)

	def check_new_step(self):
		'''Если все мячи вернулись на место, генерирует новый ряд блоков'''
		if [ball.motion for ball in self.player.balls] == [False for i in range(len(self.player.balls))] and not self.angle_line_showing:
			self.angle_line_showing = True
			self.canvas.add(self.angle_line)
			self.generate_row()

	def generate_row(self): 
		if self.angle_line_showing:
			for block in self.blocks:
				block.y -= block.size[0]
				if block._type == 'Block': block.label.center_y -= block.size[0]
				elif block._type != 'ball':
					self.remove_widget(block)
					self.blocks.remove(block)
			settings.block_health += 1
			self.create_blocks_line()




	def update_blocks(self):
		'''Обновляет блоки: цвет при ударе, проверяет поражение'''
		for block in self.blocks:
			block.update()
			self.check_game_over(block)
			if block.health <= 0:
				self.blocks.remove(block)
				self.remove_widget(block)
				if block._type == 'Block': self.remove_widget(block.label)
		min_block_y = min([block.y for block in self.blocks])

		dictionary = {range(450, 550): 0.05, range(350, 450): 0.04, range(250, 350): 0.03, range(150, 250): 0.02}
		for key, value in dictionary.items():
			if min_block_y in key:
				self.bg.anim_delay = value

	def check_game_over(self, block):
		'''Проверяет позицию блока на поражение'''
		if block.y <= 0:
			settings.block_health = settings.base_block_health
			self.remove_blocks()
			self.remove_balls()
			self.create_blocks_line()
			self.add_balls()

	def remove_blocks(self):
		'''Удаляет все блоки'''
		for block in self.blocks:
			self.remove_widget(block)
			if block._type == 'Block': self.remove_widget(block.label)
		self.blocks = []

	def remove_balls(self):
		'''Удаляет все мячи'''
		for ball in self.player.balls:
			self.remove_widget(ball)
		self.player.balls = []
	
	def on_touch_down(self, touch):
		'''Действия при нажатии'''
		self.move_balls()




	def move_balls(self):
		'''Приводит мячи в движение, если они все стоят на месте'''
		if [ball.motion for ball in self.player.balls] == [False for i in range(len(self.player.balls))]:
			for ball in self.player.balls:
				ball.motion = True
			point = self.angle_line.points[2:] #точка нажатия
			self.ball_number = 0 #номер мяча, который в данный момент отправляется
			self.ball_mover = Clock.schedule_interval(partial(self.ball_move, point), 1/15) #постепенный запуск мячей

	def ball_move(self,  point, dt):
		'''Постепенно запускает мячи'''
		self.player.balls[self.ball_number].vel_x = (point[0] - self.player.balls[self.ball_number].x)/60
		self.player.balls[self.ball_number].vel_y = (point[1] - self.player.balls[self.ball_number].y)/60
		if self.ball_number < len(self.player.balls)-1:
			self.ball_number += 1
		else:
			self.ball_mover.cancel() #если мячи закончились, то прекратить запуск мячей

	def show_angle(self, window, m_pos):
		'''Показывает линию-направление'''
		if [ball.motion for ball in self.player.balls] == [False for i in range(len(self.player.balls))]:
			self.angle_line.points = (self.player.balls[-1].center_x, self.player.balls[-1].center_y,  m_pos[0],m_pos[1])
		elif self.angle_line_showing:
			self.canvas.remove(self.angle_line)
			self.angle_line_showing = False

	def add_one_ball(self):
		'''Добавляет один новый мяч в список и на экран'''
		self.player.balls.append(Ball(settings, self))
		self.add_widget(self.player.balls[-1])

		self.player.balls[-1].center_x = settings.window_size[0]/2
		self.player.balls[-1].y = 0
		self.player.balls[-1].big_bonus = False
		self.player.balls[-1].draw_rect()




class GameApp(App):
	def build(self):
		self.game = Game()
		self.game.init_graphics()
 
		Window.bind(mouse_pos = self.game.show_angle)
		Clock.schedule_interval(self.game.update, 1/300)
		return self.game

if __name__ == '__main__':
	GameApp().run()