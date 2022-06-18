import random
import pygame
import numpy as np
import cv2

EMPTY = (10,0,34)
FILLED = (30,30,30)
DYNAMIC = (190,0,0)

game_over = False
score = 0

class Shape:
    O = ((True,True),
        (True,True))
    Z = ((True,True,False),
        (False,True,True))
    Z1 = ((False,True,True),
        (True,True,False))
    L = ((True,False,False),
        (True,True,True))
    L1 = ((False,False,True),
        (True,True,True))
    T = ((False,True,False),
        (True,True,True))
    I = ((True,True,True,True),)
    SHAPES = (O,Z,Z1,L,L1,T,I)
    def __init__(self):
        self.shape = list(random.choice(self.SHAPES))
        self.prev_shape = None
        self.posx = 0
        self.posy = 0
        self.lastposx = self.lastposy = None

    def turn(self):
        self.prev_shape = self.shape.copy()
        self.shape =  [[self.shape[j][i] for j in range(len(self.shape) - 1, -1,-1)]\
             for i in range(len(self.shape[0]))] 
    
    def go_back(self):
        self.shape = self.prev_shape.copy()
        self.prev_shape = None

    def set_pos(self,x=None,y=None):
        if x is not None:
            self.lastposx = self.posx
            self.posx = x
        if y is not None:
            self.lastposy = self.posy
            self.posy = y

    def get_pos(self):
        return self.posx, self.posy

class Box(pygame.sprite.Sprite):
    width, height = 40, 40
    def __init__(self, x, y) -> None:
        super().__init__()
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(EMPTY,pygame.Rect(1,1,self.width-2,self.height-2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.filled = False
        self.painted = False

    def update(self):
        if self.painted:
            self.painted = False
            return
        color = FILLED if self.filled else EMPTY
        self.image.fill(color,pygame.Rect(1,1,self.width-2,self.height-2))

    def paint(self):
        self.image.fill(DYNAMIC,pygame.Rect(1,1,self.width-2,self.height-2))
        self.painted = True

class Chart(pygame.sprite.Sprite):
    width, height = 480,600
    def __init__(self):
        self.chart = [[Box(x,y) for x in range(0, self.width, Box.width)] \
            for y in range(0, self.height, Box.height)]
        self.shape = None
        self.keys = []
        self.counter = 0

    def draw(self,ekran:pygame.Surface):
        for line in self.chart:
            for i in line:
                ekran.blit(i.image,i.rect)
    
    def draw_shape(self):
        for x,line in enumerate(self.shape.shape):
            for y,f in enumerate(line):
                if f:self.chart[self.shape.posx + x][self.shape.posy + y].paint()

    def update(self):
        if not self.shape:
            if not self.create_shape(): self.game_over()
        self.move_shape()
        self.draw_shape()
        self.scroll_shape()
        self.check_lines()
        self.update_chart()
        self.keys.clear()

    def update_chart(self):
        for line in self.chart:
            for i in line:
                i.update()

    def create_shape(self):
        self.shape = Shape()
        return self.check_shape(self.shape.posx,self.shape.posy)
    
    def check_shape(self,psx,psy):
        for x, line in enumerate(self.shape.shape):
            for y, i in enumerate(line):
                if not i:
                    continue
                if not 0 <= y + psy <= self.width//Box.width - 1 or \
                    not 0 <= x + psx <= self.height//Box.height - 1:
                    return False 
                if self.chart[x + psx][y + psy].filled:
                     return False
        return True

    def move_shape(self):
        x,y = self.shape.get_pos()
        #if pygame.K_UP in self.keys: x -= 1
        if pygame.K_DOWN in self.keys: x += 1
        if pygame.K_LEFT in self.keys: y -= 1
        if pygame.K_RIGHT in self.keys: y += 1
        if pygame.K_RETURN in self.keys: self.turn_shape()
        self.shape.set_pos(x,y)
        if not self.check_shape(*self.shape.get_pos()):
            self.shape.set_pos(self.shape.lastposx,self.shape.lastposy)

    def turn_shape(self):
        self.shape.turn()
        if not self.check_shape(*self.shape.get_pos()):
            self.shape.go_back()
    
    def place_shape(self):
        psx,psy = self.shape.get_pos()
        for x, line in enumerate(self.shape.shape):
            for y, i in enumerate(line):
                if not i:
                    continue
                self.chart[x + psx][y + psy].filled = i
        self.shape = None

    def scroll_shape(self):
        self.counter += 1
        if self.counter == 20:
            self.counter = 0
            self.shape.set_pos(self.shape.posx + 1,self.shape.posy)
            if not self.check_shape(*self.shape.get_pos()):
                self.shape.set_pos(self.shape.lastposx,self.shape.lastposy)
                self.place_shape()

    def check_lines(self):
        global score
        chart = [[i.filled for i in line] for line in self.chart]
        chart.reverse()
        rmvd_lines = 0
        for i,line in enumerate(chart):
            if all(line):
                chart.pop(i - rmvd_lines)
                chart.append([False for _ in range(len(chart[0]))])
                rmvd_lines += 1
        for x,line in enumerate(reversed(chart)):
            for y,i in enumerate(line):
                self.chart[x][y].filled = i
        score += rmvd_lines
            
    def game_over(self):
        global game_over
        game_over = True

def blur(image:pygame.Surface):
    w = image.get_width()
    h = image.get_height()
    kernel = (30,30)
    imgdata = pygame.surfarray.array3d(image)
    blured = cv2.blur(imgdata,kernel)
    image = pygame.surfarray.make_surface(blured)
    return image

def main():
    global game_over, score
    ekran = pygame.display.set_mode((800,600))
    clock = pygame.time.Clock()
    chart = Chart()
    pygame.font.init()
    f = pygame.font.SysFont("monospace",30,True)
    blurred_background = None
    while True:
        clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                quit()
            if ev.type == pygame.KEYDOWN:
                chart.keys.append(ev.key)
        if game_over:
            if blurred_background == None:
                blurred_background = blur(ekran)
            ekran.blit(blurred_background,(0,0))
            p = f.render("GAME OVER",True,(0,255,0))
            p2 = f.render(f"Score : {score}",True,(0,255,0))
            ekran.blit(p,((800-p.get_width())//2,(550-p.get_height())//2))
            ekran.blit(p2,((800-p2.get_width())//2,(650-p2.get_height())//2))
            if pygame.K_RETURN in chart.keys:
                chart = Chart()
                game_over = False
                score = 0
        else:
            ekran.fill((255,255,255))
            p = f.render(f" Score : {score}",True,(0,0,0),(255,255,255))
            ekran.blit(p,(Chart.width,0))
            chart.update()
            chart.draw(ekran)
        pygame.display.update()

s = pygame.Surface((800,600))
blur(s)
main()
