from kivy.uix.image import Image
from kivy.uix.label import Label
from random import randrange, choice

class Block(Image):
	def __init__(self, settings, _type, game):
		super().__init__()
		self.col = choice(['Green', 'Purple', 'Red', 'Turquoise'])
		self.size = (settings.block_size, settings.block_size)
		self.pos = (randrange(0, settings.window_size[0] - settings.block_size, settings.block_size), settings.window_size[1] - settings.block_size)
		self.anim_delay = 0.01
		self.anim_loop = 1
		while self.pos in [block.pos for block in game.blocks]:
			self.pos = (randrange(0, settings.window_size[0] - settings.block_size, settings.block_size), settings.window_size[1] - settings.block_size)
		if _type == 'Block':
			self.health = settings.block_health
			self.block_source = 'Data/'+str(self.col)+'cell.png'
			self.label = Label(text = str(self.health), center = self.center, font_size = 20, font_name = 'Impact')
		else:
			self.health = 1
			self.block_source = 'Data/bonus_'+str(_type)+'.png'
			if _type != 'ball':
				self.block_source = 'Data/back_bonus_'+str(_type)+'.gif'
		self._type = _type
		self.source = self.block_source
		self.color_timer = 0

	def update(self):
		if self.color_timer != 0:
			self.color_timer -= 1
			if self.color_timer == 0:
				if self._type != 'ball' and self._type != 'Block': self.source = self.block_source
				elif self._type == 'Block': self.anim_delay = -1

	def get_damage(self, damage):
		self.health -= damage
		self.label.text = str(int(self.label.text)-damage)
		self.source = 'Data/'+str(self.col)+'attachedcell.gif'
		self.anim_delay = 0.01
		if self.color_timer == 0: self.color_timer = 60

