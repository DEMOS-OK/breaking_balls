from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse
from random import choice

class Ball(Widget):
	def __init__(self, settings, game):
		super().__init__()
		self.center_x = settings.window_size[0]/2
		self.y = 0
		self.size = (settings.ball_size, settings.ball_size)

		self.motion = False #Двигается мяч или нет
		self.settings = settings
		self.damage = settings.ball_damage #урон мяча по блоку
		self.game = game
		self.protection = False #бонус защиты
		self.speedup = False #бонус скорости
		self.ignore = 0 #бонус игнорирования блоков (плохой бонус)

		self.damager = 0
		self.copied = False

		self.vel_x = 0 #скорости, по х и у
		self.vel_y = 0

	def draw_rect(self):
		self.rect = Ellipse(size = self.size, pos = (self.center_x-self.size[0]/2, self.y))
		self.canvas.add(self.rect)

	def move(self):
		self.center = (self.center_x + self.vel_x, self.center_y + self.vel_y)
		if self.right >= self.settings.window_size[0] or self.x <= 0:
			self.vel_x *= -1
		if self.top >= self.settings.window_size[1]:
			self.top = self.settings.window_size[1] - 1
			self.vel_y *= -1
		if self.y <= 0 and not int(self.center_x) == self.settings.window_size[0]/2 and not self.protection:
			if (self.vel_x < 0 and self.vel_y > 0) or (self.vel_x > 0 and self.vel_y < 0): self.vel_y *=-1
			self.vel_x += self.vel_y
			self.vel_y = 0
			self.y = 0
			if int(self.center_x) in range(int(self.settings.window_size[0]*38/80), int(self.settings.window_size[0]*42/80)) and self.motion:
				self.__init__(self.settings, self.game)
		elif self.protection and self.y <= 0:
			self.y = 2 #необходимо, чтобы не было одного бага
			self.vel_y *= -1 #отскок
			self.protection = False #защита выключается
		self.rect.pos = self.pos


	def check_collisions(self):
		for block in self.game.blocks:
			if self.collide_widget(block) and self.ignore == 0:
				if block._type == 'Block':
					block.get_damage(self.damage)
					self.check_collision_direction(block)
				elif self not in self.game.player.fake_balls: self.check_bonuses(block)
				if block._type == 'ball' and self not in self.game.player.fake_balls:
					block.health -= self.damage 
				if block._type != 'ball' and block._type != 'Block' and self not in self.game.player.fake_balls:
					if block.source != 'Data/attached_bonus_'+str(block._type)+'.gif':
						block.source = 'Data/attached_bonus_'+str(block._type)+'.gif'
					block.anim_delay = 0.05
					if block.color_timer == 0: block.color_timer = 60

	def check_collision_direction(self, block):
		if int(self.top) in range(block.y, int(block.center_y)) and int(self.center_x) in range(block.x, block.right):
			self.top = block.y
			self.vel_y *= -1
		if int(self.x) in range(int(block.center_x), block.right) and int(self.center_y) in range(block.y, block.top):
			self.vel_x *= -1
			self.x = block.right
		if int(self.y) in range(int(block.center_y), block.top) and int(self.center_x) in range(block.x, block.right):
			self.y = block.top
			self.vel_y *= -1
		if int(self.right) in range(block.x, int(block.center_x)) and int(self.center_y) in range(block.y, block.top):
			self.vel_x *= -1
			self.right = block.x
		self.rect.pos = self.pos

	def check_bonuses(self, block):
		if block._type == 'ball': self.game.add_one_ball() #добавляет мяч
		
		elif block._type == 'double': self.damage = 2 #урон 2

		elif block._type == 'ignore': self.ignore = 120 #игнор блоков 2 секунды

		elif block._type == 'offset': self.protection = True #бонус отскока

		elif block._type == 'speed' and not self.speedup: #ускоряет
			self.vel_x *= 1.5
			self.vel_y *= 1.5
			self.speedup = True

		elif block._type == 'lightning' and not self.big_bonus: #вызывает молнию
			self.add_big_bonus_offset('lightning')

		#собирает все не собранные мячи
		elif block._type == 'allballs' and len([cube for cube in self.game.blocks if cube._type == 'ball']) > 0:
			for cube in self.game.blocks:
				if cube._type == 'ball': cube.health -= self.damage

		elif block._type == 'random': #выбирает рандомны бонус
			block._type = choice(self.game.bonuses)
			self.check_bonuses(block)

		elif block._type == 'damager': #наносит урон всем блокам по x и y
			blocks = [cube for cube in self.game.blocks if (cube.y == block.y or cube.x == block.x) and cube._type == 'Block']
			if self.damager == 0:
				self.damager = 60
				for cube in blocks:
					cube.get_damage(1)

		elif block._type == 'bifurcation' and not self.copied: #Создаёт копию мяча
			self.copied = True
			self.game.player.fake_balls.append(Ball(self.settings, self.game))
			self.game.player.fake_balls[-1].pos = self.pos
			self.game.player.fake_balls[-1].draw_rect()
			self.game.player.fake_balls[-1].motion = True
			self.game.player.fake_balls[-1].vel_y = self.vel_y
			self.game.player.fake_balls[-1].vel_x = -self.vel_x
			self.game.add_widget(self.game.player.fake_balls[-1])

		elif block._type == 'radiation' and not self.big_bonus: #вызывает радиацию
			self.add_big_bonus_offset('radiation')

	def add_big_bonus_offset(self, bonus_name):
		if [ball.big_bonus for ball in self.game.player.balls] == [False for i in range(len(self.game.player.balls))]:
			self.game.bg.source = 'Data/start_'+bonus_name+'_bg.gif'
			self.game.bg_start = 30

		self.big_bonus = True #Если этот мяч ещё не брал бонус
		if bonus_name == 'radiation': self.game.radiation_offset += 30
		else: self.game.lightning_offset += 60